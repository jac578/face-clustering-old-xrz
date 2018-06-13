cluster_method='DBSCAN'
feature_dir=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c 
feature_list=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c\feat_list.txt 
image_dir=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c 
save_dir=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c\cluster-rlt 
eps=0.55
n_process=8

python cluster_test.py \
	--method ${cluster_method} \
	--featDir ${feature_dir} \
	--featureList ${feature_list} \
	--imgDir ${image_dir} \
	--saveResult \
	--saveDir ${save_dir} \
	--eps ${eps} \
	--nProcess ${n_process}


