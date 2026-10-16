"""Report builder (BUILD_D.md D8, contract C5). Owner: D. NOT IMPLEMENTED YET.

Contract: read artifacts/<run_id>/report.json; copy referenced screenshots into the run dir;
in report/template.html replace the exact tag  <link rel="stylesheet" href="style.css">
with an inline <style> block holding report/style.css; replace the token
/*__MIRA_REPORT_JSON__*/null  with the JSON; write artifacts/<run_id>/report.html.
Fail with a clear error if the token or the link tag is missing.
"""


def build_report(run_dir: str, template_path: str = "report/template.html", css_path: str = "report/style.css") -> str:
    raise NotImplementedError("D8: build_report")
