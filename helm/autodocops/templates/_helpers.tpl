{{/*
Common labels
*/}}
{{- define "autodocops.labels" -}}
app.kubernetes.io/name: {{ .Chart.Name }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
{{- end }}

{{/*
Selector labels for backend
*/}}
{{- define "autodocops.backend.selectorLabels" -}}
app: autodocops-backend
app.kubernetes.io/name: {{ .Chart.Name }}-backend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels for frontend
*/}}
{{- define "autodocops.frontend.selectorLabels" -}}
app: autodocops-frontend
app.kubernetes.io/name: {{ .Chart.Name }}-frontend
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Selector labels for celery worker
*/}}
{{- define "autodocops.celery.selectorLabels" -}}
app: autodocops-celery-worker
app.kubernetes.io/name: {{ .Chart.Name }}-celery
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
