from contextlib import contextmanager

from ocp_resources.persistent_volume_claim import PersistentVolumeClaim
from ocp_resources.resource import get_client
from ocp_resources.serving_runtime import ServingRuntime

client = get_client()


for sr in ServingRuntime.get(dyn_client=client):
    print(sr.name, sr.namespace)


@contextmanager
def model_pvc():
    with PersistentVolumeClaim(
        name="model-pvc",
        namespace="default",
        client=client,
        size="15Gi",
        accessmodes="ReadWriteOnce",
    ) as pvc:
        yield pvc
