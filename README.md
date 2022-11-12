# washtenaw-elections-scraper

This is a tool to retrieve election results data from Washtenaw County. The results can be found [here](https://www.washtenaw.org/314/Election-Results). 

We've used this for the [2021 Ann Arbor special elections](https://www.michigandaily.com/news/ann-arbor/city-of-ann-arbor-2021-special-election-results/), the [2022 midterm primary elections](https://specials.michigandaily.com/2022/primary-election/) and the [2022 midterm general elections](https://www.michigandaily.com/news/elections/ann-arbor-2022-midterm-election-results/).

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
