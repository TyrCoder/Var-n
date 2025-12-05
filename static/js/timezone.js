(function(window) {
  const TIME_ZONE = 'Asia/Manila';
  const HAS_TIMEZONE = /([zZ]|[+\-]\d{2}:?\d{2})$/;

  function normalizeDateInput(value) {
    if (!value && value !== 0) {
      return null;
    }
    if (value instanceof Date) {
      return isNaN(value.getTime()) ? null : value;
    }
    if (typeof value === 'number') {
      const numeric = new Date(value);
      return isNaN(numeric.getTime()) ? null : numeric;
    }
    if (typeof value === 'string') {
      const trimmed = value.trim();
      if (!trimmed) {
        return null;
      }
      let normalized = trimmed;
      if (!HAS_TIMEZONE.test(trimmed)) {
        normalized = trimmed.replace(' ', 'T');
        normalized += 'Z';
      }
      const parsed = new Date(normalized);
      if (!isNaN(parsed.getTime())) {
        return parsed;
      }
      const fallback = new Date(trimmed);
      return isNaN(fallback.getTime()) ? null : fallback;
    }
    try {
      const coerced = new Date(value);
      return isNaN(coerced.getTime()) ? null : coerced;
    } catch (err) {
      console.warn('[TimeZone] Unable to parse date value', value, err);
      return null;
    }
  }

  function formatDateTime(value, options) {
    const parsed = normalizeDateInput(value);
    if (!parsed) {
      return null;
    }
    return parsed.toLocaleString('en-PH', Object.assign({
      timeZone: TIME_ZONE,
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: true
    }, options || {}));
  }

  function formatDate(value, options) {
    const parsed = normalizeDateInput(value);
    if (!parsed) {
      return null;
    }
    return parsed.toLocaleString('en-PH', Object.assign({
      timeZone: TIME_ZONE,
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    }, options || {}));
  }

  function formatTime(value, options) {
    const parsed = normalizeDateInput(value);
    if (!parsed) {
      return null;
    }
    return parsed.toLocaleString('en-PH', Object.assign({
      timeZone: TIME_ZONE,
      hour: '2-digit',
      minute: '2-digit',
      second: undefined,
      hour12: true
    }, options || {}));
  }

  function toISOString(value) {
    const parsed = normalizeDateInput(value);
    if (!parsed) {
      return null;
    }
    const formatter = new Intl.DateTimeFormat('en-CA', {
      timeZone: TIME_ZONE,
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: false
    });
    const parts = formatter.formatToParts(parsed).reduce((acc, part) => {
      acc[part.type] = part.value;
      return acc;
    }, {});
    if (!parts.year) {
      return null;
    }
    return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}:${parts.second}+08:00`;
  }

  window.PhilippineTime = {
    format: (value, options) => {
      const parsed = normalizeDateInput(value);
      if (!parsed) {
        return null;
      }
      return parsed.toLocaleString('en-PH', Object.assign({ timeZone: TIME_ZONE }, options || {}));
    },
    formatDate,
    formatDateTime,
    formatTime,
    toISOString,
    parse: normalizeDateInput,
    TIME_ZONE
  };
})(window);
