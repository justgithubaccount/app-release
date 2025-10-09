package kubernetes

import rego.v1

# 🛡️ 1. Контейнеры должны иметь ресурсы
deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.memory
  msg := sprintf("Container %s missing memory limit", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"  
  container := input.spec.template.spec.containers[_]
  not container.resources.limits.cpu
  msg := sprintf("Container %s missing CPU limit", [container.name])
}

# 🔬 2. Должны быть probes
deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not container.livenessProbe
  msg := sprintf("Container %s missing livenessProbe", [container.name])
}

deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_] 
  not container.readinessProbe
  msg := sprintf("Container %s missing readinessProbe", [container.name])
}

# 📛 3. Namespace должен быть указан
deny contains msg if {
  not input.metadata.namespace
  msg := "Resource is missing namespace"
}

# 🔐 4. Контейнеры должны запускаться не от root
deny contains msg if {
  input.kind == "Deployment"
  not input.spec.template.spec.securityContext.runAsNonRoot
  msg := "Deployment must set runAsNonRoot: true"
}

# 📦 5. Если используется LLM — должна быть задана модель
deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  input.metadata.labels["app.kubernetes.io/name"] == "chat-api"
  not input.spec.template.metadata.annotations["openrouter.model"]
  msg := "chat-api is missing openrouter.model annotation"
}

# 🔭 6. OTEL переменные должны быть заданы
deny contains msg if {
  input.kind == "Deployment"
  container := input.spec.template.spec.containers[_]
  not has_otel_endpoint(container)
  msg := "OpenTelemetry OTLP endpoint is missing"
}

# Вспомогательная функция для проверки OTEL endpoint
has_otel_endpoint(container) if {
  some env in container.env
  env.name == "OTEL_EXPORTER_OTLP_ENDPOINT"
}