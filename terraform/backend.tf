terraform {
  backend "s3" {
    # "Key" in this terraform block will only work when you do terraform-apply from your local machine. If run using pipelines, it will be overwritting anyway for its own Key "dev.state" or "prod.state" depending:
    bucket  = "terraform-state-profile-infra-dev-725423737651-eu-central-1-an"
    key     = "fastApi_lambda/dev.tfstate"
    region  = "eu-central-1"
    encrypt = true
    # use_lockfile = true  # the new way for "state locking" will be handled natively within S3
  }
}
