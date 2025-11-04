class TimeFormats:
    # --- 常用基本格式 ---

     # YYYY-MM-DD HH:mm:ss
    DATETIME_STANDARD = '%Y-%m-%d %H:%M:%S'
    # YYYY-MM-DD HH:mm:ss.ffffff (包含微秒)
    DATETIME_WITH_MICROSECONDS = '%Y-%m-%d %H:%M:%S.%f'
    # YYYY-MM-DD
    DATE_ONLY = '%Y-%m-%d'
    # HH:mm:ss
    TIME_ONLY = '%H:%M:%S'

    # --- ISO 8601 / RFC 3339 及其变体 ---

    # RFC 3339 / ISO 8601 (不含时区，通常隐含本地时间或UTC，取决于上下文)
    # YYYY-MM-DDTHH:mm:ss
    RFC3339_NO_TZ = '%Y-%m-%dT%H:%M:%S'
    # RFC 3339 / ISO 8601 (不含时区，带微秒)
    # YYYY-MM-DDTHH:mm:ss.ffffff
    RFC3339_MICRO_NO_TZ = '%Y-%m-%dT%H:%M:%S.%f'
    # RFC 3339 / ISO 8601 UTC (Zulu time)
    # YYYY-MM-DDTHH:mm:ssZ
    # 注意：datetime 对象应为 UTC 时间，Z是字面量。
    RFC3339_UTC_ZULU = '%Y-%m-%dT%H:%M:%SZ'
    # RFC 3339 / ISO 8601 UTC (Zulu time, 带微秒)
    # YYYY-MM-DDTHH:mm:ss.ffffffZ
    # 注意：datetime 对象应为 UTC 时间，Z是字面量。
    # 在 Python 中，这通常被视为 "RFC3339Nano" 的微秒级实现。
    RFC3339_MICRO_UTC_ZULU = '%Y-%m-%dT%H:%M:%S.%fZ'
    # RFC 3339 / ISO 8601 带时区偏移 (例如: +08:00)
    # YYYY-MM-DDTHH:mm:ss+HH:MM
    # 注意：datetime 对象必须是时区感知（aware）的。
    RFC3339_WITH_OFFSET = '%Y-%m-%dT%H:%M:%S%:z'
    # RFC 3339 / ISO 8601 带时区偏移 (带微秒)
    # YYYY-MM-DDTHH:mm:ss.ffffff+HH:MM
    # 注意：datetime 对象必须是时区感知（aware）的。
    # 在 Python 中，这通常被视为 "RFC3339Nano" 的微秒级实现。
    RFC3339_MICRO_WITH_OFFSET = '%Y-%m-%dT%H:%M:%S.%f%:z'

    # --- 其他常用格式 ---

    # YYYY/MM/DD
    DATE_SLASHED = '%Y/%m/%d'
    # YYYYMMDD (紧凑日期)
    DATE_COMPACT = '%Y%m%d'
    # HH:mm (不含秒)
    TIME_SHORT = '%H:%M'
    # HH:MM AM/PM (12小时制，带AM/PM)
    TIME_12HOUR_AMPM = '%I:%M %p'
    # HH:MM:SS AM/PM (12小时制，带AM/PM和秒)
    TIME_12HOUR_AMPM_SECONDS = '%I:%M:%S %p'
    # Weekday, Month DD, YYYY HH:mm:ss (例如: Friday, October 27, 2023 15:30:00)
    FULL_DATETIME_READABLE = '%A, %B %d, %Y %H:%M:%S'
    # RFC 1123 (HTTP Date Format, 例如: Fri, 27 Oct 2023 15:30:00 GMT)
    RFC1123_HTTP_DATE = '%a, %d %b %Y %H:%M:%S GMT' # 注意：GMT是字面量
    # YYYYMMDDHHmmss (紧凑日期时间)
    DATETIME_COMPACT = '%Y%m%d%H%M%S'
    # YYYYMMDDHHmmssfff (紧凑日期时间，带微秒)
    DATETIME_COMPACT_WITH_MICROSECONDS = '%Y%m%d%H%M%S%f'

class Time(TimeFormats):
    pass