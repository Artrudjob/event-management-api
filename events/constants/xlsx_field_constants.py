from enum import StrEnum


class XlsxFieldConstants(StrEnum):
    NAME = "name"
    DESCRIPTION = "description"
    PUBLICATION_AT = "publication_at"
    STARTS_AT = "starts_at"
    ENDS_AT = "ends_at"
    RATING = "rating"
    STATUS = "status"
    VENUE_NAME = "venue_name"
    LATITUDE = "latitude"
    LONGITUDE = "longitude"


XLSX_HEADERS = {
    "название": XlsxFieldConstants.NAME,
    "описание": XlsxFieldConstants.DESCRIPTION,
    "дата и время публикации": XlsxFieldConstants.PUBLICATION_AT,
    "дата и время начала проведения": XlsxFieldConstants.STARTS_AT,
    "дата и время завершения проведения": XlsxFieldConstants.ENDS_AT,
    "название места проведения": XlsxFieldConstants.VENUE_NAME,
    "широта": XlsxFieldConstants.LATITUDE,
    "долгота": XlsxFieldConstants.LONGITUDE,
    "рейтинг": XlsxFieldConstants.RATING,
}
