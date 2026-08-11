from app.services.normalization_service import NormalizationService
from app.services.validation_service import ValidationService


class CanonicalService:

    @staticmethod
    def prepare(df):

        df = NormalizationService.normalize_columns(df)

        df = NormalizationService.normalize_strings(df)

        df = NormalizationService.normalize_dates(df)

        df = NormalizationService.normalize_amounts(df)

        df = NormalizationService.normalize_status(df)

        df = NormalizationService.remove_duplicates(df)

        ValidationService.validate_columns(df)

        return df