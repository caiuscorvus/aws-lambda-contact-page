# AWS Lambda Contact Page
### This lambda can generate and process contacts on a static website, sending those contacts using Amazon SES. The intended audience and scale is home-labbing and very low-traffic personal websites.

Pending write up, this readme will go over the entire process from creating setting up the AWS credentials, the AWS API, SES, S3 etc.

## Page Generation

The WebPage class in page-handler.py takes a template html file and inserts the main content. Not only is is useful for returning errors, repopulating forms, etc, but it could easily be extended to generate an entire (simple) website.  

