import os
import json
from sentence_transformers import SentenceTransformer, util
from tqdm import tqdm

# 使用 Sentence-BERT 模型
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# 定义文件和文件夹路径
query_file_path = 'D:\\Documents\\Desktop\\data\\query.json'
candidates_path = 'D:\\Documents\\Desktop\\data\\candidates'
output_path = 'D:\\Documents\\Desktop\\output_ranked_results.json'

# 1. 数据处理
query_cases = []
candidate_pools = {}

# 加载查询案例
print("Loading query cases...")
with open(query_file_path, 'r', encoding='utf-8') as query_file:
    for line in query_file:
        line = line.strip()
        # 跳过空行
        if not line:
            continue
        query_data = json.loads(line)
        query_id = str(query_data['ridx'])  # 把id转为字符串
        query_content = query_data['q']
        query_cases.append({"case_id": query_id, "content": query_content})

# 加载候选案例池
print("Loading candidate pool...")
candidate_folders = os.listdir(candidates_path)
with tqdm(total=len(candidate_folders), desc="Iterating through candidate folders", leave=True,
          mininterval=1) as pbar:
    for folder_name in candidate_folders:
        # 数字文件夹层
        folder_path = os.path.join(candidates_path, folder_name)
        if not os.path.isdir(folder_path):
            continue

        # .json文件层，把所有正确文件（的文件名）存入列表
        candidate_files = [f for f in os.listdir(folder_path) if f.endswith('.json')]

        candidate_cases = []
        for candidate_file in candidate_files:
            # 组合出所有.json文件完整路径
            candidate_jsonfile_path = os.path.join(folder_path, candidate_file)
            with open(candidate_jsonfile_path, 'r', encoding='utf-8') as file:
                # 加载json文件内容
                candidate_data = json.load(file)
                case = {"case_id": candidate_data.get("ajId"), "content": candidate_data.get("ajjbqk")}
                candidate_cases.append(case)
        """此处使用文件夹名作为键，如果用query_id，输出只有最后一个id和对应的100个案例排序"""
        candidate_pools[folder_name] = candidate_cases
        # 更新进度条
        pbar.update(1)

# 2.计算相似度，排序
print("Calculating similarity and sorting candidates...")
results = []

with tqdm(total=len(query_cases), desc="Processing query cases", leave=True, mininterval=1) as pbar:
    for query in query_cases:
        query_id = query['case_id']
        query_text = query['content']
        """
        从 candidate_pools 中获取与当前查询案例 ID（query_id）匹配的候选案例，如果找不到则返回一个空列表 []
        """
        candidates = candidate_pools.get(query_id, [])
        # 检查列表是否为空
        if not candidates:
            continue

        candidate_texts = [candidate['content'] for candidate in candidates]

        query_embedding = model.encode(query_text, convert_to_tensor=True)
        """返回一个矩阵，行数和列表长度（句子数量）相同"""
        candidate_embeddings = model.encode(candidate_texts, convert_to_tensor=True)

        # 计算余弦相似度并排序
        """结果矩阵的形状是 [1, num_candidates]，每个值为查询案例与各个候选案例之间的相似度分数。"""
        cos_scores = util.pytorch_cos_sim(query_embedding, candidate_embeddings)[0].cpu().tolist()
        sorted_candidates = sorted(zip(candidates, cos_scores), key=lambda x: x[1], reverse=True)

        ranked_candidates_with_scores = []
        for candidate, score in sorted_candidates:
            ranked_candidates_with_scores.append({'case_id': candidate['case_id'], 'similarity_score': score})
        results.append({'query_case_id': query_id, 'ranked_candidates': ranked_candidates_with_scores})

        pbar.update(1)

# 3. 保存结果
with open(output_path, 'w', encoding='utf-8') as file:
    json.dump(results, file, ensure_ascii=False, indent=4)

print(f"Finished！ The result has been saved to {output_path}.")
