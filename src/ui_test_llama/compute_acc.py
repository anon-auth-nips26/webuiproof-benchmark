import os
import json
import glob
from tqdm import tqdm
from collections import defaultdict

# Category mapping
CATEGORY_MAP = {
    'DDT': 'Data Display Testing',
    'FT': 'Functionality Testing',
    'DVT': 'Design Validation Testing'
}

def load_json(in_file):
    """Load JSON file"""
    with open(in_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def load_jsonl(in_file):
    """Load JSONL file"""
    datas = []
    with open(in_file, 'r', encoding='utf-8') as f:
        for line in f:
            datas.append(json.loads(line))
    return datas

def save_json(data, out_file):
    """Save data to JSON file"""
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)

def save_jsonl(datas, out_file, mode='w'):
    """Save data to JSONL file"""
    with open(out_file, mode, encoding='utf-8') as f:
        for data in datas:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')

def count_test_files(data_dir, range):
    """Count the number of test_tasks_*.jsonl files based on unique IDs * 2"""
    test_files = glob.glob(os.path.join(data_dir, 'test_response_*_final_filtered_cleaned*.json'))
    
    # Extract unique IDs from filenames
    unique_ids = set()
    for file_path in sorted(test_files):
        filename = os.path.basename(file_path)
        if filename.startswith('test_response_'):
            # Extract ID part (e.g., 000102 from test_tasks_000102-1.jsonl)
            parts = filename.replace('test_response_', '').replace('_final_filtered_cleaned*.json', '').split('-')
            if range != None:
                if len(parts) > 0 and int(parts[0]) <= range:
                    unique_ids.add(parts[0])
            else:
                if len(parts) > 0:
                    unique_ids.add(parts[0])
    
    # Return unique IDs count * 2 sampling times
    return len(unique_ids) 

def count_build_test_files(result_dir):
    """Count the number of test_tasks_*.jsonl files based on unique IDs * 2"""
    test_files = glob.glob(os.path.join(result_dir, 'test_tasks_*.jsonl'))
    
    # Extract unique IDs from filenames
    unique_ids = set()
    for file_path in test_files:
        filename = os.path.basename(file_path)
        if filename.startswith('test_tasks_'):
            # Extract ID part (e.g., 000102 from test_tasks_000102-1.jsonl)
            parts = filename.replace('test_tasks_', '').split('-')
            if len(parts) > 0:
                unique_ids.add(parts[0])
    
    # Return unique IDs count * 2 sampling times
    return len(unique_ids) 


def count_test_cases(data_dir, range):
    """Count the number of test cases based on unique IDs * 2"""
    test_files = glob.glob(os.path.join(data_dir, 'test_response_*_final_filtered_cleaned*.json'))
    
    # Track cases per unique ID
    id_cases = {}
    
    for file in sorted(test_files):
        filename = os.path.basename(file)
        if filename.startswith('test_response_'):
            # Extract ID part (e.g., 000102 from test_tasks_000102-1.jsonl)
            parts = filename.replace('test_response_', '').replace('_final_filtered_cleaned*.json', '').split('-')
            
            if range != None:
                if len(parts) > 0 and int(parts[0]) <= range:
                    unique_id = parts[0]
                    test_files = load_json(file)
                    test_cases = test_files['test_cases']
                    id_cases[unique_id] = len(test_cases['functionality_testing']) + len(test_cases['data_display_testing']) + len(test_cases['design_validation_testing'])
            else:
                if len(parts) > 0:
                    unique_id = parts[0]
                    test_files = load_json(file)
                    test_cases = test_files['test_cases']
                    id_cases[unique_id] = len(test_cases['functionality_testing']) + len(test_cases['data_display_testing']) + len(test_cases['design_validation_testing'])
    # Calculate total cases (sum of cases per unique ID)
    total_cases = sum(id_cases.values())
    return total_cases

def extract_category_from_folder(folder_name):
    """Extract category from folder name (e.g., task000102-1_DDT_TC001 -> DDT)"""
    parts = folder_name.split('_')
    if len(parts) >= 2:
        category_code = parts[1]
        return CATEGORY_MAP.get(category_code, category_code)
    return 'Unknown'

def analyze_results(result_dir, num_test_files, num_test_cases):
    """Analyze the test results from interact_message.json files"""
    # Get all test case folders
    folders = [f for f in os.listdir(result_dir) if os.path.isdir(os.path.join(result_dir, f)) and 'task' in f]
    
    # Count unique IDs for total calculation
    # unique_ids = set()
    # for folder in folders:
    #     if 'task' in folder:
    #         parts = folder.split('_')
    #         if len(parts) > 0:
    #             task_part = parts[0].replace('task', '')
    #             if '-' in task_part:
    #                 unique_id = task_part.split('-')[0]
    #                 unique_ids.add(unique_id)
    
    # Calculate total based on unique IDs * 2

    
    # Initialize counters
    total_build_results = {'build_success': 0, 'total': num_test_files,  'build_fail': 0}
    total_results = {'yes': 0, 'no': 0, 'partial': 0, 'total_test_cases': num_test_cases, 'build_fail_test_cases': 0}
    category_results = defaultdict(lambda: {'yes': 0, 'no': 0, 'partial': 0, 'total_test_cases': 0, 'build_fail_test_cases': 0})
    
    total_build_results['build_success'] = count_build_test_files(result_dir)
    total_build_results['build_fail'] = total_build_results['total'] - total_build_results['build_success']

    # Process each folder
    for folder in tqdm(folders, desc='Processing test cases'):
        # Extract category
        category = extract_category_from_folder(folder)
        
        # Check for interact_messages.json
        message_file = os.path.join(result_dir, folder, 'interact_messages.json')
        if not os.path.exists(message_file):
            print(f'Warning: interact_messages.json not found in {folder}, skipping...')
            continue
        
        # Load and analyze the messages
        try:
            messages = load_json(message_file)
            
            # Find the last assistant message
            result = 'no'  # Default to NO if no clear result found
            for message in reversed(messages):
                if message['role'] == 'assistant':
                    content = message['content']
                    if 'YES' in content:
                        result = 'yes'
                        break
                    elif 'PARTIAL' in content:
                        result = 'partial'
                        break
                    elif 'NO' in content:
                        result = 'no'
                        break
            
            # Update counters
            total_results[result] += 1
            category_results[category][result] += 1
            
        except Exception as e:
            print(f'Error processing {folder}: {e}')
    
    # Calculate build fail for total and categories
    total_results['build_fail_test_cases'] = total_results['total_test_cases'] - total_results['yes'] - total_results['no'] - total_results['partial']
    
    # Update category totals and build_fail
    for category in category_results:
        # Calculate category total based on proportion of folders in this category
        category_folder_count = sum(1 for f in folders if extract_category_from_folder(f) == category)
        category_proportion = category_folder_count / len(folders) if len(folders) > 0 else 0
        category_results[category]['total_test_cases'] = int(total_results['total_test_cases'] * category_proportion)
        
        # Calculate build fail
        category_results[category]['build_fail_test_cases'] = (category_results[category]['total_test_cases'] - 
                                                 category_results[category]['yes'] - 
                                                 category_results[category]['no'] - 
                                                 category_results[category]['partial'])
    
    return total_build_results, total_results, category_results

def generate_report(total_build_results, total_results, category_results, output_dir, model_name):
    """Generate report with the analysis results"""
    # Calculate rates
    total = total_results['total_test_cases']
    yes_rate = total_results['yes'] / total * 100 if total > 0 else 0
    no_rate = total_results['no'] / total * 100 if total > 0 else 0
    partial_rate = total_results['partial'] / total * 100 if total > 0 else 0
    build_fail_rate = total_build_results['build_fail'] / total_build_results['total'] * 100 if total > 0 else 0
    
    # Create summary report
    summary = {
        'total_sampe': total_build_results['total'],
        'total_build_sucess': total_build_results['build_success'],
        'total_build_fail': total_build_results['build_fail'],
        'total_test_cases': total,
        'yes_count': total_results['yes'],
        'no_count': total_results['no'],
        'partial_count': total_results['partial'],
        'build_fail_test_cases': total_results['build_fail_test_cases'],
        'yes_rate': yes_rate,
        'no_rate': no_rate,
        'partial_rate': partial_rate,
        'build_fail_rate': build_fail_rate
    }
    
    # Create category report
    categories = {}
    for category, results in category_results.items():
        cat_total = results['total_test_cases']
        categories[category] = {
            'total': cat_total,
            'yes_count': results['yes'],
            'no_count': results['no'],
            'partial_count': results['partial'],
            'build_fail_count': results['build_fail_test_cases'],
            'yes_rate': results['yes'] / cat_total * 100 if cat_total > 0 else 0,
            'no_rate': results['no'] / cat_total * 100 if cat_total > 0 else 0,
            'partial_rate': results['partial'] / cat_total * 100 if cat_total > 0 else 0,
            'build_fail_rate': results['build_fail_test_cases'] / cat_total * 100 if cat_total > 0 else 0
        }
    
    # Create full report
    report = {
        'summary': summary,
        'categories': categories
    }
    
    # Save report as JSON
    save_json(report, os.path.join(output_dir, 'results', f'{model_name}_analysis_results.json'))
    
    # Create markdown tables
    md_report = '# Test Results Analysis\n\n'
    
    # Summary table
    md_report += '## Summary\n\n'
    md_report += '| Total Test Cases | Yes | No | Partial | Build Fail | Yes Rate | No Rate | Partial Rate | Build Fail Rate |\n'
    md_report += '|------------------|-----|----|---------|-----------|---------:|--------:|-------------:|---------------:|\n'
    md_report += f'| {total} | {total_results["yes"]} | {total_results["no"]} | {total_results["partial"]} | {total_results["build_fail_test_cases"]} | {yes_rate:.2f}% | {no_rate:.2f}% | {partial_rate:.2f}% | {build_fail_rate:.2f}% |\n\n'
    
    # Category table
    md_report += '## Results by Category\n\n'
    md_report += '| Category | Total | Yes | No | Partial | Build Fail | Yes Rate | No Rate | Partial Rate | Build Fail Rate |\n'
    md_report += '|----------|-------|-----|----|---------|-----------|---------:|--------:|-------------:|---------------:|\n'
    
    for category, results in sorted(category_results.items()):
        cat_total = results['total_test_cases']
        yes_rate = results['yes'] / cat_total * 100 if cat_total > 0 else 0
        no_rate = results['no'] / cat_total * 100 if cat_total > 0 else 0
        partial_rate = results['partial'] / cat_total * 100 if cat_total > 0 else 0
        
        build_fail_rate = results['build_fail_test_cases'] / cat_total * 100 if cat_total > 0 else 0
        md_report += f'| {category} | {cat_total} | {results["yes"]} | {results["no"]} | {results["partial"]} | {results["build_fail_test_cases"]} | {yes_rate:.2f}% | {no_rate:.2f}% | {partial_rate:.2f}% | {build_fail_rate:.2f}% |\n'
    
    # Save markdown report
    # with open(os.path.join(output_dir, 'analysis_results.md'), 'w', encoding='utf-8') as f:
    #     f.write(md_report)
    
    return report, md_report

        
def main():
    """Main function"""
    from argparse import ArgumentParser
    
    parser = ArgumentParser(description='Analyze WebUI test results')
    parser.add_argument('--in_dir', type=str, help='Input directory containing results')
    parser.add_argument('--data_dir', type=str, help='Input directory containing results')
    parser.add_argument('--eval_name', type=str, help='Evaluation name')
    parser.add_argument('--model_name', type=str, help='Model name')
    parser.add_argument('--range', type=int, help='number of project')

    args = parser.parse_args()
    
    # Set result directory
    result_dir = os.path.join(args.in_dir, 'results', args.model_name)

    # Set data folder directory
    data_dir = args.data_dir
    
    sampling_num = 1

    # Step 1: Count test files (webpages)
    num_test_files = count_test_files(data_dir, args.range)
    print(f'Number of test files (webpages): {num_test_files}')
    
    num_test_files = num_test_files * sampling_num

    # # Step 2: Count test cases
    num_test_cases = count_test_cases(data_dir, args.range)
    print(f'Total number of test cases: {num_test_cases}')

    num_test_cases = num_test_cases * sampling_num
    

    # # Step 3 & 4: Analyze results and categorize
    print('Analyzing test results...')
    total_build_results, total_results, category_results = analyze_results(result_dir, num_test_files, num_test_cases)
    
    # Generate Sand save report
    report, md_report = generate_report(total_build_results, total_results, category_results, args.in_dir, args.model_name)
    
    # # Print summary
    # print('\nAnalysis complete!')
    # print(f'Total test cases: {total_results["total"]}')
    # print(f'YES: {total_results["yes"]} ({total_results["yes"]/total_results["total"]*100:.2f}%)')
    # print(f'NO: {total_results["no"]} ({total_results["no"]/total_results["total"]*100:.2f}%)')
    # print(f'PARTIAL: {total_results["partial"]} ({total_results["partial"]/total_results["total"]*100:.2f}%)')
    # print(f'BUILD FAIL: {total_results["build_fail"]} ({total_results["build_fail"]/total_results["total"]*100:.2f}%)')
    # print('\nResults by category:')
    
    # for category, results in sorted(category_results.items()):
    #     cat_total = results['total']
    #     yes_rate = results['yes'] / cat_total * 100 if cat_total > 0 else 0
    #     no_rate = results['no'] / cat_total * 100 if cat_total > 0 else 0
    #     partial_rate = results['partial'] / cat_total * 100 if cat_total > 0 else 0
        
    #     print(f'{category}: YES={yes_rate:.2f}%, NO={no_rate:.2f}%, PARTIAL={partial_rate:.2f}%')
    
    # print(f'\nDetailed reports saved to {args.in_dir}/analysis_results.json and {args.in_dir}/analysis_results.md')

    
if __name__ == '__main__':
    main()