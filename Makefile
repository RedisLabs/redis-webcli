.PHONY: push
push: memtier_benchmark
	cf push

memtier_benchmark:
	wget https://s3.eu-central-1.amazonaws.com/redislabs-dev-public-deps/binaries/memtier_benchmark_1.2.15_xenial
	mv memtier_benchmark_1.2.15_xenial memtier_benchmark
	chmod +x memtier_benchmark
