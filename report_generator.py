from jinja2 import Template

def generate_html_report(financial_records):
    # Load the Jinja2 template from a file (report_template.html)
    with open("templates/report.html", "r") as template_file:
        template_content = template_file.read()

    # Create a Jinja2 Template object
    template = Template(template_content)

    # Render the template with financial records data
    html_content = template.render(financial_records=financial_records)

    return html_content