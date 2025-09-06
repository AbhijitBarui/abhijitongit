from datetime import date, timedelta

WD = ["MO","TU","WE","TH","FR","SA","SU"]

def _in_range(d, start, end):
    if start and d < start: return False
    if end and d > end: return False
    return True

def occurs_on(task, d: date) -> bool:
    if not _in_range(d, task.start_date, task.end_date): return False
    if str(d) in (task.skip_dates or []): return False
    rec = task.recurrence or "none"
    if rec == "none":
        return True  # one-time; you decide how to surface it (e.g., until scheduled)
    if rec == "daily":
        if not task.start_date: return True
        delta = (d - task.start_date).days
        return delta >= 0 and delta % max(task.recur_interval,1) == 0
    if rec == "weekdays":
        return d.weekday() < 5
    if rec == "weekends":
        return d.weekday() >= 5
    if rec == "weekly":
        if not task.start_date: return True
        # interval by whole weeks from start_date same weekday set
        weeks = (d - task.start_date).days // 7
        if weeks < 0 or (weeks % max(task.recur_interval,1)) != 0:
            return False
        if task.recur_weekdays:
            want = set(x.strip().upper() for x in task.recur_weekdays.split(",") if x.strip())
            return WD[d.weekday()] in want
        return True
    if rec == "monthly":
        # by day-of-month
        dom = task.recur_monthday or (task.start_date.day if task.start_date else d.day)
        return d.day == dom and _monthly_interval_ok(task, d)
    if rec == "custom":
        # keep simple now; later you can parse rrule_text
        return False
    return False

def _monthly_interval_ok(task, d: date) -> bool:
    if not task.start_date: return True
    # months since start_date (approx)
    months = (d.year - task.start_date.year) * 12 + (d.month - task.start_date.month)
    return months >= 0 and months % max(task.recur_interval,1) == 0
