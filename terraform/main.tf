terraform {
  required_version = ">= 1.7.0, < 2.0.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }
}

# Configure the AWS Provider using the "default" profile located in my ~/.aws/credentials, and adding Tags:
provider "aws" {
  profile = "infra-dev-admin"
  region  = "eu-central-1"

  default_tags {
    tags = {
      CreatedBy = "Terraform"
    }
  }
}
