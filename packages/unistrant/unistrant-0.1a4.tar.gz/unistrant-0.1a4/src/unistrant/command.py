import datetime
import itertools
import logging
import shutil
import uuid
from abc import ABC, abstractmethod
from collections.abc import Generator

from unistrant.http import CertificateAuthentication, HttpProtocol
from unistrant.options import Options
from unistrant.record import Record, RecordDocument, RecordFile
from unistrant.sams import SamsClient

logger = logging.getLogger(__name__)


class BaseCommand(ABC):
    def __init__(self, options: Options):
        super().__init__()
        self.options = options
        self.error = False

        authentication = CertificateAuthentication(options.sams_certificate, options.sams_key)
        protocol = HttpProtocol(authentication)
        self.sams = SamsClient(options.sams_url, protocol)

    @abstractmethod
    def run(self) -> None:
        pass

    def fail(self) -> None:
        if not self.error:
            self.error = True


class RegisterCommand(BaseCommand):
    def __init__(self, options: Options):
        super().__init__(options)

        self.record_files = {RecordFile(path) for path in self.options.records_directory.iterdir() if path.is_file()}

    @property
    def records(self) -> Generator[Record, None, None]:
        for file in self.record_files:
            yield from file.records

    @property
    def record_documents(self) -> Generator[RecordDocument, None, None]:
        for record_type, iterator in itertools.groupby(self.records, key=lambda record: record.record_type):
            for records in itertools.batched(iterator, 100):
                yield RecordDocument(record_type, records)

    def run(self) -> None:
        documents = set(self.record_documents)
        failed_documents = set()

        for document in documents:
            try:
                self.sams.upload_record_document(document)
            except Exception as e:
                logger.error(f"Error uploading document: {str(e)}")
                failed_documents.add(document)
                self.fail()

        for file in self.record_files:
            self.archive(file)

        for document in failed_documents:
            self.save_for_later(document)

    def save_for_later(self, document: RecordDocument) -> None:
        destination = self.options.records_directory / f"error-{str(uuid.uuid4())}.xml"
        logger.debug(f"Saving {len(document.records)} records to {destination} for later attempt")
        with destination.open("wb") as f:
            f.write(document.bytes)

    def archive(self, file: RecordFile) -> None:
        if (destination := self.options.archive_directory / file.name).exists():
            timestamp = datetime.datetime.now(datetime.UTC).astimezone().isoformat()
            destination = destination.with_name(f"{file.name}-{timestamp}")
        logger.debug(f"Archiving {file.name} to {destination}")
        shutil.move(file.path, destination)
