import xml.etree.ElementTree as ET
import dateutil.parser
import pytz

def parse_submitted_job_xml(xml_text):
    root = ET.fromstring(xml_text)

    def get_text(tag):
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    return {
        "job_handle": get_text("jobHandle"),
        "job_stage": get_text("jobStage"),
        "terminal_stage": get_text("terminalStage"),
        "date_submitted": get_text("dateSubmitted"),
    }

def parse_checked_job_xml(xml_text):
    root = ET.fromstring(xml_text)

    def get_text(tag):
        el = root.find(tag)
        return el.text.strip() if el is not None and el.text else ""

    def get_uri(tag):
        el = root.find(tag)
        if el is None:
            return ""
        url_el = el.find("url")
        return url_el.text.strip() if url_el is not None and url_el.text else ""

    job_name = ""
    metadata = root.find("metadata")
    if metadata is not None:
        entry = metadata.find("entry")
        if entry is not None:
            value = entry.find("value")
            if value is not None and value.text:
                job_name = value.text.strip()

    date_submitted = get_text("dateSubmitted")
    date_submitted_cet = date_submitted
    if date_submitted:
        try:
            date_submitted_cet = (
                dateutil.parser.parse(date_submitted)
                .astimezone(pytz.timezone("CET"))
                .strftime("%d/%m/%Y %H:%M:%S")
            )
        except Exception:
            pass

    return {
        "job_name": job_name,
        "job_stage": get_text("jobStage"),
        "terminal_stage": get_text("terminalStage"),
        "failed": get_text("failed"),
        "date_submitted": date_submitted,
        "date_submitted_cet": date_submitted_cet,
        "results_uri": get_uri("resultsUri"),
    }

def parse_results_listing(xml_text):
    root = ET.fromstring(xml_text)
    files = []

    for child in root:
        if child.tag != "jobfiles":
            continue

        for jobchild in child:
            if jobchild.tag != "jobfile":
                continue

            item = {"name": "", "url": ""}

            for node in jobchild:
                if node.tag == "filename" and node.text:
                    item["name"] = node.text.strip()

                elif node.tag == "downloadUri":
                    for uri_child in node:
                        if uri_child.tag == "url" and uri_child.text:
                            item["url"] = uri_child.text.strip()

            if item["name"] and item["url"]:
                files.append(item)

    return files

def parse_list_jobs_xml(xml_text):
    root = ET.fromstring(xml_text)
    jobs = []

    jobs_root = root.find("jobs")
    if jobs_root is None:
        return jobs

    for job in jobs_root.findall("jobstatus"):
        self_uri_el = job.find("selfUri")
        if self_uri_el is None:
            continue

        url_el = self_uri_el.find("url")
        title_el = self_uri_el.find("title")

        self_uri = url_el.text.strip() if url_el is not None and url_el.text else ""
        title = title_el.text.strip() if title_el is not None and title_el.text else ""

        if self_uri:
            handle = self_uri.rstrip("/").split("/")[-1]
            jobs.append({
                "handle": handle,
                "title": title or handle,
                "self_uri": self_uri,
            })

    return jobs