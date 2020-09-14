#!/bin/bash

if [ $# -eq 0 ]
then
	echo "ERROR: Please pass the torpedo yaml file to proceed"
	exit 1
fi
KDM="kubectl delete -n metacontroller"

for i in $@
do
	torpedo_yaml=$i
	
	name=`grep "^  name: " $torpedo_yaml | awk '{print $2}'`

	kubectl delete -f $torpedo_yaml

	jobs=`kubectl get jobs -n metacontroller | grep $name | awk '{print $1}'`
	$KDM job $jobs

	cm=`grep "^    cluster-config:" -A3 $torpedo_yaml | awk '/name:/ {print $2}'`
	if [ -z $cm ]
	then
		$KDM cm remote-cluster-kube-config
	else
		$KDM cm $cm
	fi
	
	volume_name=`grep "^    volume-name:" $torpedo_yaml | awk '{print $2}'| sed -e "s/[\'\"]//g"`
	$KDM pvc $volume_name
	pods=`kubectl get pods -n metacontroller | grep $name | awk '{print $1}'`
	$KDM pods $pods
done
