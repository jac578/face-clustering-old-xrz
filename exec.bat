SETLOCAL ENABLEDELAYEDEXPANSION

SET cluster_method="DBSCAN"
REM SET feature_dir="C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c"
REM SET feature_list="C:\zyf\00_Ataraxia\facex\suzhoutai-test-imgs\cluster_and_evaluation\5b0f996b7bcb36000761a80c\feat_list.txt"
SET feature_dir="./data/feats_npy_v3"
SET feature_list="./data/feat_list.txt"

SET save_dir="./rlt-imgs"
REM image_list当中每行的图片需要跟feature_list中每一行的特征一一对应
SET image_dir="./data/imgs_aligned_112x112"
SET image_list="./data/img_list.txt"
SET eps=0.55
SET n_process=2

python cluster_test.py ^
	--method %cluster_method% ^
	--featDir %feature_dir% ^
	--featureList %feature_list% ^
	--saveDir %save_dir% ^
	--imgDir %image_dir% ^
	--imgList %image_list% ^
	--eps %eps% ^
	--nProcess %n_process% ^
	--saveResult

pause
