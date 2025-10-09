terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_owner
}

data "github_repository" "repo" {
  name = "app-release"
}

resource "github_branch_protection" "main" {
  repository_id = data.github_repository.repo.node_id
  pattern       = "main"

  # Запретить пуш без PR
  required_pull_request_reviews {
    required_approving_review_count = 0
  }

  # Запрет force push:
  # allows_force_pushes = false

  # Запрет удаления ветки:
  # allows_deletions = false

  # Требовать, чтобы админы тоже подчинялись защите:
  enforce_admins = true

  # Обязательные CI-проверки перед мержем:
  # required_status_checks {
  #   strict   = true
  #   contexts = ["helm", "opa", "ci"] # ← названия из GitHub Checks
  # }
}
