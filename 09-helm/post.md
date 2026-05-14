# Kubernetes Helm Chart 완전 정복: simple-file-server 실습을 통해 배우기

## 서론: 왜 Helm을 사용하는가?

쿠버네티스를 실무에서 사용하다 보면 비슷한 구조의 매니페스트 파일을 계속 작성해야 하는 상황에 직면하게 됩니다. 예를 들어:

```bash
# 개발 환경
kubectl apply -f namespace.yaml
kubectl apply -f configmap.yaml
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
kubectl apply -f ingress.yaml

# 스테이징 환경 (같은 파일 복사 후 수정)
kubectl apply -f staging-namespace.yaml
kubectl apply -f staging-configmap.yaml
...
```

이런 복사-붙여넣기 방식은 관리하기 어렵고 실수가 발생하기 쉽습니다. 여기서 **Helm**이 등장합니다. Helm은 쿠버네티스용 패키지 매니저로, 템플릿화된 매니페스트를 재사용 가능한 패키지(Chart)로 만들어 주는 도구입니다.

이 포스트에서는 `simple-file-server` 애플리케이션을 Helm Chart로 패키징한 실제 예제를 통해 Helm의 개념과 사용법을 상세히 설명합니다.

---

## Helm Chart 기초 개념

### Helm이란?

Helm은 "쿠버네티스 애플리케이션을 위한 패키지 매니저"로 설명할 수 있습니다. 패키지 매니저로서 다음과 같은 장점을 제공합니다:

- **재사용성**: 한 번 작성한 템플릿을 다양한 환경(개발, 스테이징, 프로덕션)에서 사용
- **버전 관리**: 애플리케이션 버전과 배포 버전을 분리하여 관리
- **값 기반 설정**: `values.yaml` 파일만 수정하면 동일한 템플릿으로 다른 설정 배포 가능

### Chart 구조

Helm Chart는 다음과 같은 구조를 가집니다:

```
chart/
├── Chart.yaml          # 차트 메타데이터 (이름, 버전, 설명 등)
├── values.yaml         # 기본 설정값들
└── templates/          # 쿠버네티스 매니페스트 템플릿들
    ├── _helpers.tpl    # 재사용 가능한 템플릿 함수들
    ├── namespace.yaml
    ├── configmap.yaml
    ├── deployment.yaml
    ├── service.yaml
    ├── ingress.yaml
    └── serviceaccount.yaml
```

---

## Chart 디렉토리 구조 상세 설명

### 1. Chart.yaml - 차트 메타데이터

```yaml
apiVersion: v2
name: simple-file-server
description: Helm chart that packages the Lesson 08 Ingress example.
type: application
version: 0.1.0      # Helm Chart 버전
appVersion: "1.0.0" # 실제 애플리케이션 버전
```

| 필드 | 설명 |
|------|------|
| `apiVersion` | Helm Chart API 버전 (현재 v2) |
| `name` | 차트 이름 |
| `description` | 차트 설명 |
| `type` | 차트 타입 (application, library 등) |
| `version` | Helm Chart 자체 버전 (CI/CD에서 관리) |
| `appVersion` | 패키징된 애플리케이션 버전 |

### 2. values.yaml - 기본 설정값

values.yaml은 Chart의 "변수" 정의 파일입니다. 이 파일을 수정하거나 오버라이드하여 다양한 환경에 배포할 수 있습니다.

```yaml
namespace:
  name: file-server
  create: true

image:
  repository: ghcr.io/jung-geun/simple-file-server
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 1

config:
  port: 3001
  logPath: /var/log/app.log
  uploadDir: /var/uploads

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi

service:
  type: ClusterIP
  port: 80
  targetPort: 3001

ingress:
  enabled: true
  className: traefik
  hosts:
    - host: file.test.com
      paths:
        - path: /
          pathType: Prefix
```

### 3. templates/_helpers.tpl - 템플릿 헬퍼 함수

재사용 가능한 네이밍과 레이블 함수들을 정의합니다.

```yaml
{{- define "simple-file-server.fullname" -}}
{{- $name := default .Chart.Name .Values.nameOverride -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}
```

| 헬퍼 함수 | 역할 |
|----------|------|
| `simple-file-server.name` | 차트의 기본 이름 |
| `simple-file-server.fullname` | 리소스 이름 (예: file-server-simple-file-server) |
| `simple-file-server.labels` | 쿠버네티스 표준 레이블 |
| `simple-file-server.selectorLabels` | 셀렉터용 레이블 |
| `simple-file-server.namespace` | 네임스페이스 이름 |
| `simple-file-server.configName` | ConfigMap 이름 |

---

## values.yaml 심층 분석

### 네임스페이스 설정

```yaml
namespace:
  name: file-server
  create: true
```

- `name`: 배포할 네임스페이스 이름
- `create`: `true`이면 Helm이 네임스페이스를 자동 생성

### 이미지 설정

```yaml
image:
  repository: ghcr.io/jung-geun/simple-file-server
  tag: latest
  pullPolicy: IfNotPresent
```

- `repository`: 이미지 저장소
- `tag`: 이미지 태그 (환경별로 다르게 설정 가능)
- `pullPolicy`: 이미지 풀 정책 (`Always`, `IfNotPresent`, `Never`)

### ConfigMap 설정

```yaml
config:
  port: 3001
  logPath: /var/log/app.log
  uploadDir: /var/uploads
```

애플리케이션 환경변수로 주입될 값들을 정의합니다.

### 리소스 설정

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi
```

- `requests`: Pod 실행을 위해 필요한 최소 리소스
- `limits`: Pod가 사용할 수 있는 최대 리소스

### Service 설정

```yaml
service:
  type: ClusterIP
  port: 80
  targetPort: 3001
```

- `type`: 서비스 타입 (`ClusterIP`, `NodePort`, `LoadBalancer`)
- `port`: 서비스 포트 (외부 접근용)
- `targetPort`: 컨테이너 포트

### Ingress 설정

```yaml
ingress:
  enabled: true
  className: traefik
  annotations:
    traefik.ingress.kubernetes.io/router.tls: "false"
  hosts:
    - host: file.test.com
      paths:
        - path: /
          pathType: Prefix
```

- `enabled`: Ingress 생성 여부
- `className`: Ingress 컨트롤러 클래스 (Traefik, Nginx 등)
- `annotations`: Ingress 컨트롤러별 설정
- `hosts`: 라우팅 규칙 (다중 호스트/경로 가능)

---

## 템플릿 헬퍼 함수 활용

### 네이밍 규칙

Helm 템플릿은 Go 템플릿 문법을 사용합니다. `_helpers.tpl`에서 정의한 헬퍼 함수는 다음과 같이 호출됩니다:

```yaml
# deployment.yaml
metadata:
  name: {{ include "simple-file-server.fullname" . }}
  namespace: {{ include "simple-file-server.namespace" . }}
  labels:
{{ include "simple-file-server.labels" . | indent 4 }}
```

### 조건부 렌더링

```yaml
# namespace.yaml - 네임스페이스 생성 여부에 따라 렌더링
{{- if .Values.namespace.create -}}
apiVersion: v1
kind: Namespace
metadata:
  name: {{ include "simple-file-server.namespace" . }}
{{- end -}}
```

### 반복문

```yaml
# ingress.yaml - 다중 호스트 처리
{{- range .Values.ingress.hosts }}
    - host: {{ .host }}
      http:
        paths:
{{- range .paths }}
          - path: {{ .path }}
            pathType: {{ default "Prefix" .pathType }}
{{- end }}
{{- end }}
```

### 값 삽입

```yaml
# configmap.yaml
data:
  PORT: "{{ .Values.config.port }}"
  LOG_PATH: "{{ .Values.config.logPath }}"
  UPLOAD_DIR: "{{ .Values.config.uploadDir }}"
```

---

## 실제 배포 예제

### 1. 템플릿 미리보기

실제 배포 전에 렌더링 결과를 확인할 수 있습니다:

```bash
cd 09-helm
helm template file-server ./chart --namespace file-server
```

이 명령어는 실제 쿠버네티스 매니페스트를 출력합니다.

### 2. 기본 배포

```bash
helm upgrade --install file-server ./chart \
  --namespace file-server \
  --create-namespace
```

- `upgrade --install`: 설치되어 있으면 업그레이드, 없으면 새로 설치
- `--namespace`: 네임스페이스 지정
- `--create-namespace`: 네임스페이스 자동 생성

### 3. Values 오버라이드

#### 개별 값 오버라이드

```bash
helm upgrade --install file-server ./chart \
  --namespace file-server \
  --set image.tag=v1.0.1 \
  --set replicaCount=3
```

#### 파일로 오버라이드

`staging-values.yaml` 파일을 생성하여 배포:

```yaml
# staging-values.yaml
image:
  tag: latest

ingress:
  hosts:
    - host: staging.file.test.com
      paths:
        - path: /
          pathType: Prefix

nodeSelector:
  kubernetes.io/hostname: "worker-1"
```

```bash
helm upgrade --install file-server ./chart \
  --namespace file-server \
  -f staging-values.yaml
```

### 4. 배포 확인

```bash
# 모든 리소스 확인
kubectl get all -n file-server

# Ingress 확인
kubectl get ingress -n file-server

# 접속 테스트
curl http://file.test.com/
```

### 5. 릴리스 관리

```bash
# 설치된 릴리스 목록
helm list -n file-server

# 릴리스 히스토리
helm history file-server -n file-server

# 롤백
helm rollback file-server -n file-server

# 삭제
helm uninstall file-server -n file-server
```

---

## 확장 팁

### 다양한 환경 설정

| 환경 | values 파일 |
|------|-------------|
| 개발 | `dev-values.yaml` (replicaCount: 1) |
| 스테이징 | `staging-values.yaml` (replicaCount: 2) |
| 프로덕션 | `prod-values.yaml` (replicaCount: 3, HPA 활성화) |

### 다중 도메인 구성

```yaml
ingress:
  hosts:
    - host: file.test.com
      paths:
        - path: /
          pathType: Prefix
    - host: admin.test.com
      paths:
        - path: /admin
          pathType: Prefix
```

### 노드 선택 및 어피니티

```yaml
nodeSelector:
  node-role.kubernetes.io/worker: "true"

affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchLabels:
              app.kubernetes.io/name: simple-file-server
          topologyKey: kubernetes.io/hostname
```

### TLS 설정

```yaml
ingress:
  tls:
    - secretName: file-server-tls
      hosts:
        - file.test.com
```

---

## 결론

Helm Chart를 사용하면 쿠버네티스 매니페스트를 효율적으로 관리할 수 있습니다:

1. **재사용성**: 한 번 작성한 템플릿으로 다양한 환경에 배포
2. **관리 용이성**: `values.yaml`만 수정하면 설정 변경 가능
3. **버전 관리**: Chart 버전과 앱 버전 분리로 릴리스 관리 용이
4. **확장성**: 다중 환경, 다중 도메인 구성 등 유연한 확장 가능

이 실습 예제인 `simple-file-server` Chart를 시작점으로 자신의 애플리케이션에 맞게 수정하여 Helm의 강력한 기능을 활용해 보세요!

## 참고 자료

- [Helm 공식 문서](https://helm.sh/docs/)
- [Helm Best Practices](https://helm.sh/docs/chart_best_practices/)
- [Kubernetes Ingress Documentation](https://kubernetes.io/docs/concepts/services-networking/ingress/)
