import pandas as pd
from datasets import load_dataset
import random
import json
import os

def process_duplicate_detection_dataset(generate_prompts=False, extract_num=100):
    df = pd.read_csv(
    "MRPC/MRPC/msr_paraphrase_train.txt",
    sep="\t",
    engine="python",         
    quoting=3,               
    )
    sample_df = df.sample(n=20, random_state=42)  
    sample_df = sample_df[["Quality", "#1 String", "#2 String"]]
    sample_df.to_csv("duplicate.csv")  
    prompt_instructions = []
    for index, d in sample_df.iterrows():
        s = template_data.replace('[$SENTENCE1$]', d['#1 String'])
        s = s.replace('[$SENTENCE2$]', d['#2 String'])
        prompt_instructions.append(s)
    if generate_prompts:
        with open('duplicate_prompts.json', 'w') as f:
            json.dump(prompt_instructions, f)


def process_grammar_correction_dataset(generate_prompts=False, extract_num=100):
    dataset = load_dataset("jfleg")['test']
    prompt_instructions = []
    random.seed(42)
    sampled = random.sample(list(dataset), 20)
    with open('grammar_correction/dev.src', 'w') as f_src, \
         open('grammar_correction/dev.ref0', 'w') as f_r0, \
         open('grammar_correction/dev.ref1', 'w') as f_r1, \
         open('grammar_correction/dev.ref2', 'w') as f_r2, \
         open('grammar_correction/dev.ref3', 'w') as f_r3:
         for item in sampled:
            s = item['sentence'].strip()
            prompt_instructions.append(template_data.replace('[$SENTENCE$]', s))
            f_src.write(s + "\n")
            f_r0.write(item['corrections'][0].strip() + '\n')
            f_r1.write(item['corrections'][1].strip() + '\n')
            f_r2.write(item['corrections'][2].strip() + '\n')
            f_r3.write(item['corrections'][3].strip() + '\n')
    if generate_prompts:
        with open('grammar_correction_prompts.json', 'w') as f:
            json.dump(prompt_instructions, f)
    print('extracting data into grammar_correction/')

def process_hate_detection_dataset(generate_prompts=False, extract_num=100):
    prompt_instructions = []
# - NEITHER: Neutral or innocuous content.'
    dataset = load_dataset("hate_speech_offensive")['train']
    random.seed(42)
    sampled = random.sample(list(dataset), 20)
    for s in sampled:
        prompt_instructions.append(template_data.replace('[$TWEET$]', s['tweet']))
    with open('hate_detection_prompts.json', 'w') as f:
        json.dump(prompt_instructions, f)
    if generate_prompts:
        with open('hate_detection.json', 'w') as f:
            json.dump(sampled, f)
    

def process_natural_language_inference_dataset(generate_prompts=False, extract_num=100):
    prompt_instructions = []
    from datasets import load_dataset
    dataset = load_dataset("glue", "rte")['train']

    random.seed(42)
    sampled = random.sample(list(dataset), 20)
    for s in sampled:
        temp = template_data.replace('[$PREMISE$]', s['sentence1']).replace('[$HYPOTHESIS$]', s['sentence2'])
        prompt_instructions.append(temp)

    with open('natural_language_inference.json', 'w') as f:
        json.dump(sampled, f)
    if generate_prompts:
        with open('natural_language_inference_prompts.json', 'w') as f:
            json.dump(prompt_instructions, f)


def process_sentiment_analysis_dataset(generate_prompts=False, extract_num=100):

    prompt_instructions = []
    dataset = load_dataset("glue", "sst2")['train']
    random.seed(42)
    sampled = random.sample(list(dataset), 20)
    for s in sampled:
        prompt_instructions.append(template_data.replace('[$SENTENCE$]', s['sentence']))
    with open('sentiment_analysis.json', 'w') as f:
        json.dump(sampled, f)
    if generate_prompts:
        with open('sentiment_analysis_prompts.json', 'w') as f:
            json.dump(prompt_instructions, f)

def generate_ground_truth(data_folder):
    tasks = ['duplicate', 'grammar_correction', 'hate_detection', 'natural_language_inference', 'sentiment_analysis']
    ground_truth = {}
    for t in tasks:
        prompt_file = os.path.join(data_folder, f'{t}_prompts.json')
        with open(prompt_file, 'r') as f:
            prompts = json.load(f)
        
        if t == 'duplicate':
            df = pd.read_csv(os.path.join(data_folder, "duplicate.csv"))
            results = df['Quality']
            for k, v in zip(prompts, results):
                r = 'Yes' if v == 1 else 'No'
                ground_truth[k] = r

        if t == 'grammar_correction':
            for i, p in enumerate(prompts):
                ground_truth[p] = i

        if t == 'natural_language_inference':
            with open(os.path.join(data_folder, 'natural_language_inference.json'), 'r') as f:
                data = json.load(f)
            for k, v in zip(prompts, data):
                r = 'Yes' if v['label'] == 0 else 'No'
                ground_truth[k] = r

        if t == 'sentiment_analysis':
            with open(os.path.join(data_folder, 'sentiment_analysis.json'), 'r') as f:
                data = json.load(f)
            for k, v in zip(prompts, data):
                r = 'positive' if v['label'] == 1 else 'negative'
                ground_truth[k] = r
        
        if t == 'hate_detection':
            with open(os.path.join(data_folder, 'hate_detection.json'), 'r') as f:
                data = json.load(f)
            for k, v in zip(prompts, data):
                r = 'No' if v['class'] == 2 else 'Yes'
                ground_truth[k] = r
    with open(os.path.join(data_folder, 'ground_truth.json'), 'w') as f:
        json.dump(ground_truth, f)
    return ground_truth

if __name__ == '__main__':
    process_duplicate_detection_dataset(generate_prompts=True)
    process_grammar_correction_dataset(generate_prompts=True)
    # process_hate_detection_dataset(generate_prompts=True)
    # process_natural_language_inference_dataset(generate_prompts=True)
    # process_sentiment_analysis_dataset(generate_prompts=True)
