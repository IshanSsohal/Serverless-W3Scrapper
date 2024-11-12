import requests
from bs4 import BeautifulSoup
import json
import boto3
from datetime import datetime

# Initialize the SNS client
sns = boto3.client('sns')
topic_arn = 'arn:aws:sns:us-east-1:533267254695:scrappertopic'  # I put my SNS topic ARN


def scrape_w3schools():
    url = "http://example.example"
    response = requests.get(url)
    response.raise_for_status()  # checks that the request was successful
    soup = BeautifulSoup(response.content, 'html.parser')

    tutorials = []

    # find tutorial links in the main navigation section of the page
    sections = soup.select('a.w3-bar-item.w3-button')

    for section in sections:
        title = section.get_text(strip=True)
        link = section['href']
        if not link.startswith('http'):
            link = f"https://www.w3schools.com{link}"  # convert relative URL to absolute

        tutorials.append({
            'title': title,
            'link': link
        })

    return tutorials


def lambda_handler(event, context):
    try:
        # Scrape the data
        scraped_data = scrape_w3schools()

        if not scraped_data:
            raise Exception("No data scraped; please check the scraper function.")

        # Save data to S3
        s3 = boto3.client('s3')
        bucket_name = 'pfc710-isohal2'  # this is my bucket name
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M")
        file_name = f"{timestamp}.json"

        # Upload the scraped data to S3
        s3.put_object(
            Bucket=bucket_name,
            Key=file_name,
            Body=json.dumps(scraped_data),
            ContentType='application/json'
        )
        print(f"Data successfully stored in {file_name}.")
        return {
            'statusCode': 200,
            'body': f"Data successfully stored in {file_name}"
        }

    except Exception as e:
        # Log the error and send an SNS notification
        error_message = f"this confirms error occured: {str(e)}"
        print(error_message)

        # Publish the error to SNS
        sns.publish(
            TopicArn=topic_arn,
            Subject='Lambda Function Error Alert',
            Message=error_message
        )

        return {
            'statusCode': 500,
            'body': f"Failed to store data: {str(e)}"
        }


if __name__ == "__main__":
    # for testing in local environment
    scraped_data = scrape_w3schools()
    print(json.dumps(scraped_data, indent=2))
