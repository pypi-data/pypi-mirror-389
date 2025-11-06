# Standard Library Imports
import os
import sys
import numpy as np
import pandas as pd
from tqdm import tqdm
from joblib import Parallel, delayed
from sklearn import metrics
from concurrent.futures import ThreadPoolExecutor, as_completed
import plotly.graph_objects as go
from IPython.display import HTML
from pandarallel import pandarallel  # Importing pandarallel for parallel processing

# Setting up the path for the module
sys.path.insert(0, os.path.dirname(os.path.realpath('__file__')))
sys.path.insert(1, '../')

# Local Imports
from config import conf as cfg
from tools import btools








# Read CSV files serially
def read_10fold_res_csv_files(file_paths):
    return [pd.read_csv(file, sep='\t') for file in file_paths]

def process_no_res(res_list, eckey, rxnkey):
    # 遍历 res_list 中的每个数据帧，计算总条目数、无预测条目数和无反应 EC 条目数
    summary = [
        [
            len(pred_detail),
            len(pred_detail[pred_detail[eckey].str.contains('NO-PREDICTION')]),
            len(pred_detail[pred_detail[rxnkey].str.contains('EC-WITHOUT-REACTION')])
        ]
        for pred_detail in res_list
    ]
    
    # 创建 DataFrame 返回结果
    return pd.DataFrame(summary, columns=['test_size', 'no_prediction', 'ec_without_rxn'])


# 并行执行标签创建的函数
def make_10folds_labels(resdf, columns_dict, rxn_label_dict, fold_num=10):
    res = []
    for i in tqdm(range(fold_num)):
        
        for src_col, lb in columns_dict.items():
            resdf[i][lb] = resdf[i][src_col].apply(lambda reaction_id: btools.make_label(reaction_id=str(reaction_id), rxn_label_dict=rxn_label_dict))
        resdf[i]['run_fold'] = i+1
        # res = res +  resdf[i]
    resdf = pd.concat(resdf, axis=0).reset_index(drop=True)
    return resdf
    


# Function to calculate metrics
def calculate_metrics(eva_df, ground_truth_col, pred_col, eva_name, avg_method='weighted'):
    res =  btools.rxn_eva_metric_with_colName(eva_df=eva_df, col_groundtruth=ground_truth_col, col_pred=pred_col, eva_name=eva_name, average_type=avg_method)
    res.insert(0, 'evaName', eva_name)
    return res

# 多线程运行评价函数
def calculate_metrics_parallel(res_df, ground_truth_col, pred_col, avg_method='weighted', max_workers=None):
    def run_metric_evaluation(index):
        return calculate_metrics(eva_df=res_df[index], ground_truth_col=ground_truth_col, pred_col=pred_col, eva_name=f'fold{index + 1}', avg_method=avg_method)
    
    results = [None] * len(res_df)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_metric_evaluation, i): i
            for i in range(len(res_df))
        }
        for future in as_completed(futures):
            i = futures[future]
            results[i] = future.result()
            
    results = pd.concat(results,axis=0).reset_index(drop=True)
    
    return results


#region 展开获取均值方差
def get_fold_mean_std_metrics(input_df):
    # 对数值列进行分组聚合
    res_fold_std = input_df[['baselineName', 'avgType','mAccuracy', 'mPrecision', 'mRecall', 'mF1']]
    # 对每个 baselineName 进行分组并计算均值和标准差
    res_fold_std = res_fold_std.groupby(['baselineName','avgType']).agg(['mean', 'std'])
    # 重置索引以简化处理
    res_fold_std = res_fold_std.reset_index()
    
    
    # 修改列名，将 MultiIndex 转换为单层列名
    res_fold_std.columns = ['_'.join(filter(None, col)).strip() for col in res_fold_std.columns]
    # 使用 melt 方法将列转换为行
    res_fold_std_melted = res_fold_std.melt(id_vars=['baselineName', 'avgType'], var_name='Metric_Statistic', value_name='Value')
    # 将 'Metric_Statistic' 列分割成 'Metric' 和 'Statistic'
    res_fold_std_melted[['Metric', 'Statistic']] = res_fold_std_melted['Metric_Statistic'].str.rsplit('_', n=1, expand=True)
    
    res_fold_std_melted = res_fold_std_melted.sort_values(by=['baselineName',  'Metric', 'avgType']).reset_index(drop=True)
    res_fold_std_melted = res_fold_std_melted.drop(columns=['Metric_Statistic'])
    
    # 使用 pivot 将数据转换为所需格式
    res_fold_std_pivot = res_fold_std_melted.pivot_table(index=['baselineName','avgType', 'Metric'], columns='Statistic', values='Value').reset_index()
    res_fold_std_pivot.columns.name = None
    return res_fold_std_pivot
#endregion

#region 统计没有预测结果和有EC没反应的结果
def statistic_no_res(res_df, name_col_ec, name_col_rxn, type='ec'):
    if type == 'ec':
        grouped_counts = res_df.groupby('run_fold').agg(
        test_size=('run_fold', 'count'),
        no_prediction_count=(name_col_ec, lambda x: (x == 'NO-PREDICTION').sum()),
        ec_without_reaction_count=(name_col_rxn, lambda x: (x == 'EC-WITHOUT-REACTION').sum())
        ).reset_index()
        
    if type == 'rxn':
        grouped_counts = res_df.groupby('run_fold').agg(
        test_size=('run_fold', 'count'),
        no_prediction_count=(name_col_rxn, lambda x: (x == 'NO-PREDICTION').sum())
        ).reset_index()
    
    return grouped_counts
#endregion







def get_simi_Pred(pred_list, uniprot_rxn_dict, topk=3):
    uniprot_id_list = [item[0] for item in pred_list][:topk]
    rxn_ids = [uniprot_rxn_dict.get(uniprot_id) for uniprot_id in uniprot_id_list]
    rxn_res = (cfg.SPLITER).join(set(rxn_ids))
    return rxn_res


    


def calculate_metrics_multi_joblib(groundtruth, predict, average_type, print_flag=False, n_jobs=4):
    # 检查数据是否为多标签分类
    is_multilabel = len(groundtruth.shape) > 1 and groundtruth.shape[1] > 1

    # 如果不是多标签分类，移除 'samples' 选项
    if average_type == 'samples' and not is_multilabel:
        raise ValueError("Samplewise metrics are not available outside of multilabel classification.")

    # 定义评估指标
    metric_functions = [
        lambda gt, pr: metrics.accuracy_score(gt, pr),
        lambda gt, pr: metrics.precision_score(gt, pr, average=average_type, zero_division=True),
        lambda gt, pr: metrics.recall_score(gt, pr, average=average_type, zero_division=True),
        lambda gt, pr: metrics.f1_score(gt, pr, average=average_type, zero_division=True)
    ]

    # 并行计算各指标
    results = Parallel(n_jobs=n_jobs)(
        delayed(metric_fn)(groundtruth, predict) for metric_fn in metric_functions
    )

    if print_flag:
        print(f'{results[0]:.6f}\t{results[1]:.6f}\t{results[2]:.6f}\t{results[3]:.6f}\t{average_type:>12s}')

    return results + [average_type]

def eva_one_fold(eva_df, lb_groundtruth, lb_predict, fold_num=None, n_jobs=4):
    # 提取 groundtruth 和 predict 数据
    groundtruth = np.stack(eva_df[lb_groundtruth])
    predict = np.stack(eva_df[lb_predict])

    # 确定数据是否为多标签
    is_multilabel = len(groundtruth.shape) > 1 and groundtruth.shape[1] > 1

    # 定义需要计算的平均类型
    average_types = ['weighted', 'micro', 'macro']
    if is_multilabel:
        average_types.append('samples')  # 仅在多标签分类中添加 'samples'

    # 并行计算不同的平均类型
    results = Parallel(n_jobs=n_jobs)(
        delayed(calculate_metrics_multi_joblib)(
            groundtruth=groundtruth,
            predict=predict,
            average_type=avg_type,
            print_flag=False,
            n_jobs=1  # 内部不再嵌套并行，避免资源争用
        ) for avg_type in average_types
    )

    # 处理结果并创建 DataFrame
    res = pd.DataFrame(results, columns=['mAccuracy', 'mPrecision', 'mRecall', 'mF1', 'avgType'])
    if fold_num is not None:
        res.insert(0, 'runFold', fold_num)

    return res


# 执行多折交叉验证
def eva_cross_validation(res_df, lb_groundtruth, lb_predict, num_folds=10):

    eva_metrics = []
    for runfold in tqdm(range(1, num_folds+1)):
        res = eva_one_fold(eva_df=res_df[res_df.run_fold==runfold].reset_index(drop=True), lb_groundtruth=lb_groundtruth, lb_predict=lb_predict,fold_num=runfold)
        eva_metrics = eva_metrics + [res]
        
    eva_metrics = pd.concat(eva_metrics, axis=0).reset_index(drop=True)
    
    return eva_metrics