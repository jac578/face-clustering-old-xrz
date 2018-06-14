cluster_method='DBSCAN'
#feature_dir=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c 
#feature_list=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c\feat_list.txt 
#image_dir=C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c 
feature_dir="./data/feats_npy_v3"
feature_list="./data/feat_list.txt"
save_dir="./rlt-imgs"

### image_list当中每行的图片需要跟feature_list中每一行的特征一一对应
image_dir="./data/imgs_aligned_112x112"
image_list="./data/img_list.txt"

eps=0.55
n_process=2

python cluster_test.py \
	--method ${cluster_method} \
	--featDir ${feature_dir} \
	--featureList ${feature_list} \
	--saveResult \
	--saveDir ${save_dir} \
	--imgDir ${image_dir} \
	--imgList ${image_list} \
	--eps ${eps} \
	--nProcess ${n_process}


