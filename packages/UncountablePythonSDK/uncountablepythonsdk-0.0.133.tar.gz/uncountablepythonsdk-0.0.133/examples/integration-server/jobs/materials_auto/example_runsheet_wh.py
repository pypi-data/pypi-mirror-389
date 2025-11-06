from io import BytesIO

from uncountable.core.file_upload import DataFileUpload, FileUpload
from uncountable.integration.job import JobArguments, RunsheetWebhookJob, register_job
from uncountable.types import (
    download_file_t,
    entity_t,
    identifier_t,
    webhook_job_t,
)


@register_job
class StandardRunsheetGenerator(RunsheetWebhookJob):
    def build_runsheet(
        self,
        *,
        args: JobArguments,
        payload: webhook_job_t.RunsheetWebhookPayload,
    ) -> FileUpload:
        args.logger.log_info("Retrieving pre-exported runsheet file from async job")

        file_query = download_file_t.FileDownloadQueryEntityField(
            entity=entity_t.EntityIdentifier(
                type=entity_t.EntityType.ASYNC_JOB,
                identifier_key=identifier_t.IdentifierKeyId(id=payload.async_job_id),
            ),
            field_key=identifier_t.IdentifierKeyRefName(
                ref_name="unc_async_job_export_runsheet_recipe_export"
            ),
        )

        downloaded_files = args.client.download_files(file_query=file_query)

        file_data = downloaded_files[0].data.read()
        return DataFileUpload(
            data=BytesIO(file_data),
            name=downloaded_files[0].name,
        )
