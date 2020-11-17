# local-fs-provisioner

This is a helper Python script which runs as a service on each worker node in my bare-metal k8s cluster. It watches for newly created PVCs with storage_class 'local-storage' and with a 'kubernetes.io/hostname' annotation, which specifices nodename the service should create & mount fs volume. Once the fs volume gets created and mounted, the local volume provisioner operator will kick-in (https://github.com/kubernetes-sigs/sig-storage-local-static-provisioner) and handle PV creation so that the PVC can bind to it. 

*This is a rather naive implementation mainly for learning k8s purposes only. In addition it saves me some time required for logging into the nodes and creating manually fs volumes of the right size for the PV/PVC creation later.*
