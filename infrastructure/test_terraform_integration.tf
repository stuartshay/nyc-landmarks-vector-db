# Test Terraform file to verify VS Code integration
resource "null_resource" "test" {
  triggers = {
    timestamp = timestamp()
  }
}

output "test_output" {
  value = "Terraform VS Code integration is working!"
}
