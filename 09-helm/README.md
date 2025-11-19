# 09. Helm으로 Ingress 실습 패키징하기

08-ingress 실습에서 작성했던 `Namespace → ConfigMap → Deployment → Service → Ingress` 파이프라인을 Helm 차트로 묶어 반복 배포를 쉽게 만드는 방법을 정리했습니다. 동일한 매니페스트를 복붙하지 않고 값만 바꿔 다양한 환경(도메인, 포트, 노드 등)에 투입하는 것이 목표입니다.

## 1. 차트 구조

```
09-helm/
└── chart/
	 ├── Chart.yaml                  # 차트 메타데이터
	 ├── values.yaml                 # 실습 기본 값 (08-ingress 매니페스트를 그대로 반영)
	 └── templates/
		  ├── _helpers.tpl            # 이름/레이블/네임스페이스 헬퍼
		  ├── namespace.yaml          # 선택적 네임스페이스 생성
		  ├── configmap.yaml          # PORT/LOG_PATH/UPLOAD_DIR 설정
		  ├── deployment.yaml         # simple-file-server Pod 정의
		  ├── service.yaml            # ClusterIP 서비스
		  ├── ingress.yaml            # file.test.com 라우팅 규칙
		  └── serviceaccount.yaml     # 필요 시 ServiceAccount 생성
```

## 2. values.yaml 핵심

- `namespace`: 기본값 `file-server`, `create: true` 로 실습 네임스페이스를 자동 생성합니다.
- `image`, `replicaCount`: 08강에서 사용한 이미지를 그대로 사용하며 원하는 태그/레플리카만 조정하면 됩니다.
- `config`: ConfigMap 데이터 (`PORT`, `LOG_PATH`, `UPLOAD_DIR`) 를 한 곳에서 정의합니다.
- `resources`, `affinity`: 기본값으로 `node-role.kubernetes.io/control-plane`/`node-role.kubernetes.io/master` 라벨이 없는 노드(=worker)에만 스케줄됩니다. 필요 시 라벨을 추가하거나 `values.yaml` 의 `affinity` 블록을 덮어써서 세밀하게 조정하세요.
- `service`, `ingress`: 이전 실습의 `service.yaml`, `ingress.yaml` 내용을 값 기반으로 재현했습니다. 호스트/클래스/경로를 자유롭게 추가할 수 있습니다.

### Worker 노드에만 배치하고 싶다면?

K3s server 노드(마스터)는 기본적으로 `node-role.kubernetes.io/control-plane`, `node-role.kubernetes.io/master` 라벨을 가지고 있으므로, 기본 `affinity` 값만으로도 Pod가 워커 노드에만 스케줄됩니다. 만약 명시적인 워커 라벨을 붙이고 싶다면 다음처럼 라벨링 후 `values.yaml` 을 덮어쓰면 됩니다.

```bash
kubectl label node worker-1 node-role.kubernetes.io/worker=true --overwrite
```

```yaml
nodeSelector:
	node-role.kubernetes.io/worker: "true"
affinity: {}
```

## 3. 템플릿 매핑

| 템플릿            | 설명                                                                                                                                             |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `namespace.yaml`  | `namespace.create` 가 true일 때만 생성. Helm 설치 시 `--namespace file-server --create-namespace` 플래그와 함께 사용하면 안전합니다.             |
| `configmap.yaml`  | values의 `config` 블록을 그대로 key/value 로 변환합니다.                                                                                         |
| `deployment.yaml` | 08강 Deployment 매니페스트를 Helmify. ConfigMap 참조, `nodeSelector`, `resources`, `imagePullSecrets` 등을 값으로 노출했습니다.                  |
| `service.yaml`    | 항상 `fullname-svc` 이름으로 ClusterIP 서비스를 생성합니다. 포트·타겟포트 모두 values로 제어합니다.                                              |
| `ingress.yaml`    | `ingress.enabled` 플래그와 `hosts` 배열을 이용해 여러 호스트/경로를 선언할 수 있도록 범용화했습니다. 기본값은 `file.test.com` 과 `/` 경로입니다. |

템플릿마다 `simple-file-server.labels` 헬퍼를 사용해 공통 레이블을 부여하므로 `kubectl get all -l app.kubernetes.io/instance=file-server` 처럼 한번에 조회할 수 있습니다.

## 4. 실습 플로우

1. **도메인 준비**: 로컬 K3s라면 `/etc/hosts` 에 마스터 노드 IP를 매핑합니다.

   ```bash
   sudo sh -c 'echo "<MASTER_NODE_IP> file.test.com" >> /etc/hosts'
   ```

2. **템플릿 미리보기**: 원본 매니페스트와 동일하게 렌더링되는지 확인합니다.

   ```bash
   cd 09-helm
   helm template file-server ./chart --namespace file-server
   ```

3. **배포**: `helm upgrade --install` 로 네임스페이스부터 Ingress까지 한 번에 배포합니다.

   ```bash
   helm upgrade --install file-server ./chart \
     --namespace file-server \
     --create-namespace
   ```

4. **검증**: 08강에서 했던 kubectl/curl 확인을 Helm 버전에서도 동일하게 수행합니다.

   ```bash
   kubectl get all -n file-server
   kubectl get ingress -n file-server
   curl http://file.test.com/
   ```

5. **정리**: 더 이상 사용하지 않을 때는 `helm uninstall file-server -n file-server` 와 `kubectl delete ns file-server` 로 리소스를 정리합니다.

## 5. 응용 미션

1. `values.yaml` 의 `ingress.hosts` 배열에 `/upload` 경로를 추가하여 정적 파일 업로드를 별도 경로로 분리해 보세요.
2. `affinity` 조건을 수정하거나 커스텀 워커 라벨을 이용해 다양한 노드 배치 시나리오를 실험해 보세요.
3. 실습 서버를 `file.test.com` / `admin.test.com` 두 도메인으로 동시에 노출하는 Helm override 파일을 만들어 `helm upgrade` 시 `-f admin-values.yaml` 옵션을 적용해 보세요.

## 6. 차트 구성 파일 & 설정 가이드

| 파일                  | 역할                                                                                                                                                                                                                                                                                       | 어떻게 조정하나요? |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------ |
| `Chart.yaml`          | 차트 이름, 버전, 앱 버전을 정의합니다. CI/CD 에서 차트 버전을 올릴 때 `version`, 실제 애플리케이션 릴리스 버전을 바꿀 때 `appVersion` 을 수정하세요.                                                                                                                                       |
| `values.yaml`         | 모든 기본 설정값. 새로운 환경이나 도메인에 배포할 때 override 파일(`-f staging.yaml`)을 추가해 각 값을 덮어쓰면 됩니다.                                                                                                                                                                    |
| `_helpers.tpl`        | 네이밍/레이블 헬퍼. 함수 이름을 변경했다면 템플릿에서도 동일하게 호출하도록 맞춰야 합니다.                                                                                                                                                                                                 |
| `namespace.yaml`      | `namespace.create=true`일 때만 네임스페이스를 생성합니다. 이미 존재하는 네임스페이스로 배포한다면 `create`를 false로 두고 `helm upgrade` 시 `--namespace` 로 지정하세요.                                                                                                                   |
| `configmap.yaml`      | `values.config` 의 PORT/LOG_PATH/UPLOAD_DIR 을 ConfigMap으로 내려줍니다. 새 환경변수를 추가하고 싶다면 `config` 블록과 템플릿의 `data` 섹션을 같이 늘리세요.                                                                                                                               |
| `deployment.yaml`     | Pod 스펙을 정의합니다. `image`, `replicaCount`, `podAnnotations`, `podSecurityContext`, `securityContext`, `resources`, `nodeSelector`, `tolerations`, `affinity` 값이 그대로 반영됩니다. 필요 시 `values.yaml` 에 새 필드를 추가하고 템플릿에 `{{- with ... }}` 패턴으로 주입하면 됩니다. |
| `service.yaml`        | `service.type/port/targetPort` 로 ClusterIP 또는 다른 타입을 지정합니다. NodePort가 필요하면 `type: NodePort` 와 함께 `nodePort` 필드를 포트 블록에 추가하세요.                                                                                                                            |
| `ingress.yaml`        | `ingress.enabled` 가 true일 때 호스트/경로 별 규칙을 생성합니다. TLS 인증서를 쓰려면 `ingress.tls` 배열에 `secretName`, `hosts` 를 채우고 `className` 을 컨트롤러에 맞게 맞추세요.                                                                                                         |
| `serviceaccount.yaml` | `serviceAccount.create=true` 인 경우에만 생성합니다. 특정 계정을 쓰려면 `create=false`, `name=<existing-sa>` 로 덮어쓰세요.                                                                                                                                                                |

### values.yaml 세부 항목

- `namespace`: 네임스페이스 이름과 생성 여부 설정.
- `image`: 저장소/태그/풀 정책. M1/M2 테스트용 이미지라면 `tag` 를 `macos.*` 로, 리눅스 클러스터는 `latest` 같은 태그로 덮어씁니다.
- `replicaCount`: 원하는 Pod 수. HPA 사용 시 기본값 1에서 시작해 HorizontalPodAutoscaler가 값을 조정하도록 둡니다.
- `imagePullSecrets`: 프라이빗 레지스트리를 쓸 때 `[{name: ghcr-cred}]` 처럼 기입하세요.
- `serviceAccount`: 별도 권한이 필요하면 `create=true` 로 두고 `annotations` 에 IAM 바인딩 등을 추가합니다.
- `podAnnotations`, `podSecurityContext`, `securityContext`: 사이드카 툴링이나 런타임 보안 옵션(예: fsGroup, runAsNonRoot)을 여기서 정의합니다.
- `config`: Deployment가 참조하는 ConfigMap 데이터. 포트를 바꾸면 `service.targetPort` 도 함께 조정해야 합니다.
- `resources`: 요청/제한. 리소스 쿼터가 없는 테스트 클러스터라면 비워도 되지만, 운영에서는 CPU/메모리를 명시하세요.
- `nodeSelector` / `tolerations` / `affinity`: 특정 노드(예: 워커)나 태인트된 노드에만 배포할 때 사용합니다. 현재 README 5절의 예시처럼 워커 라벨을 붙여 사용하면 됩니다.
- `service`: Ingress 백엔드가 바라보는 내부 서비스. 타입을 `LoadBalancer` 나 `NodePort` 로 바꾸면 외부 노출 방식도 함께 바뀝니다.
- `ingress`: 호스트, 경로, TLS, 클래스, 애노테이션을 모두 값으로 제어합니다. Traefik 외 컨트롤러를 쓸 경우 `className` 과 애노테이션 키를 해당 컨트롤러 형식으로 바꾸세요.

새로운 환경을 만들고 싶다면 아래와 같이 override 파일을 만들어 `helm upgrade` 시 추가하면 됩니다.

```yaml
# staging-values.yaml
image:
	tag: latest
ingress:
	hosts:
		- host: staging.file.test.com # 접속할 도메인으로 변경
			paths:
				- path: /
					pathType: Prefix

nodeSelector:
  kubernetes.io/hostname: "worker-1" # 각 노드의 호스트네임에 맞게 수정
```

```bash
helm upgrade --install file-server ./chart \
	--namespace file-server \
	--create-namespace \
	-f override-values.yaml
```

이 구조를 이해하면, values 파일과 템플릿 몇 군데만 수정해도 새 앱이나 환경을 빠르게 배포할 수 있습니다.

이 README만 따라도 08-ingress 실습을 Helm 차트로 재현하고, 값만 교체해 다른 환경으로 확장하는 전체 흐름을 강의 형태로 진행할 수 있습니다.
