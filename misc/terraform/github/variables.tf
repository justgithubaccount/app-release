variable "github_token" {
  description = "GitHub token with admin access"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub username or organization"
  type        = string
}
