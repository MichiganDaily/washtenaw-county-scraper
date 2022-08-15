# washtenaw-elections-scraper

> ⚠️ Do not delete `data.json` (for now). [City of Ann Arbor 2021 Special Election Results](https://www.michigandaily.com/news/ann-arbor/city-of-ann-arbor-2021-special-election-results/) still relies on it as a URL.

This is a tool to retrieve election results data from Washtenaw County. The results can be found [here](https://www.washtenaw.org/314/Election-Results).

Previously, this scraper was configured to run through GitHub Actions. It is now configured to run as an AWS Lambda function.

## Local development

You'll need a Python version >= 3.9 for [`zoneinfo`](https://docs.python.org/3/library/zoneinfo.html).

1. Create a virtual environment by running `python -m venv venv`.
2. Activate your virtual environment by running `source venv/bin/activate`.
3. Install dependencies by running `pip install -r requirements.txt`.
4. Run the scraper with `ENVIRONMENT=local python main.py`.

## Production notes

- Use Python 3.9 as the runtime and x86_64 as the architecture.
- Use an execution role with access to S3.
- Add an EventBridge (CloudWatch Events) trigger with a schedule expression.
- Add the following environment variables to your Lambda configuration:
   ```plaintext
   ENVIRONMENT=production
   BUCKET=subdomain.domain.com
   KEY=directory/filename
   ```
- Upload `lambda_handler.py` to the code section.
- You may need to change the timeout in general configurations.
- You may need to add layers for external packages.
