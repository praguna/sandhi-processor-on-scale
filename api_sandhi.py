import requests
import re
import tqdm
import sandhi
import pandas as pd

# global sandhi object
S = sandhi.Sandhi() 

def get_sandhi_lib(word1_wx, word2_wx):
    data =  S.sandhi(word1_wx, word2_wx)
    if len(data) > 0:
        return [item[0] for item in data]
    return ["No data found in the response."] 

# Function to call the API and get the saMhiwapaxam field
def get_sandhi(word1_wx, word2_wx):
    url = "https://sanskrit.uohyd.ac.in/cgi-bin/scl/sandhi/sandhi_json.cgi"
    params = {
        "word1": word1_wx,
        "word2": word2_wx,
        "encoding": "Unicode",
        "outencoding": "Unicode"
    }

    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            # return data[-1].get("saMhiwapaxam", None)
            return [item.get("saMhiwapaxam") for item in data]
        else:
            return ["No data found in the response."]
    else:
        return [f"Failed to retrieve data. HTTP Status code: {response.status_code}"]
    

def merge_words_depth(words):
    results = []
    def explore(i, curr_sandhi):
        if i == len(words):
            if curr_sandhi.find(">") != -1 or curr_sandhi.find("<") != -1: return
            results.append(curr_sandhi)
            return
        
        ## FOR API CALL
        # sandhis = get_sandhi(curr_sandhi, words[i])
        # for sandhi in sandhis:
        #     explore(i+1 , sandhi.encode('latin1').decode('utf-8'))

        ## FOR LIB CALL
        sandhis = get_sandhi_lib(curr_sandhi, words[i])
        for sandhi in sandhis:
            sandhi = sandhi.replace("Z", "ऽ")
            explore(i+1 , sandhi)

    explore(1, words[0])
    return ", ".join(results)


def merge_words(words):
    if len(words) == 1:
        return words[0]
    # Start with the first word
    result = words[0]
    
    # Iterate through the remaining words
    for word in words[1:]:
        result = get_sandhi(result, word).encode('latin1').decode('utf-8')
    
    return result

# Function to clean text by removing unwanted characters and diacritical marks
def clean_text(text):
    # Remove unwanted diacritical marks, specific characters, and numeric characters
    cleaned_text = re.sub(r'[॥\[\]०-९]', '', text)  # Remove danda (॥), square brackets, and numeric characters
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Replace multiple spaces with a single space
    cleaned_text = cleaned_text.strip()  # Remove leading and trailing whitespace
    return cleaned_text

# Function to preprocess the verse by removing text within specific delimiters
def preprocess_verse(verse):
    # Remove text within square brackets [] and || ||
    verse = re.sub(r'\[\[.*?\]\]', '', verse)  # Remove text within [[ ]]
    verse = re.sub(r'\|\|.*?\|\|', '', verse)  # Remove text within || ||

    # Clean up text by removing unwanted characters and diacritical marks
    verse = clean_text(verse)
    
    return verse


# Define a function to split verse into units based on punctuation and spaces
def split_verse(verse):
    # Preprocess the verse
    verse = preprocess_verse(verse)

    # Split by punctuations and multiple spaces while keeping the delimiters
    parts = re.split(r'(\s+|।|॥|१|२|३|४|५|६|७|८|९|०)', verse)
    
    # Clean up empty strings, whitespace, numeric elements and specific unwanted characters
    cleaned_parts = [part.strip() for part in parts if part.strip() and not re.match(r'^[०-९]+$', part) and part not in ['[', ']']]
    
    # Group the parts into lists where each list represents a segment between punctuations
    segments = []
    current_segment = []
    
    for part in cleaned_parts:
        if part in ['।', '॥']:
            if current_segment:
                segments.append(current_segment)
                current_segment = []
        else:
            current_segment.append(part)
    
    if current_segment:
        segments.append(current_segment)
    
    return segments


def raw_text_processor():
    ### From raw text #########
    # From docx file
    from docx import Document
    file_path = '/Users/pragunamanvi/Downloads/rjm2.docx'
    document = Document(file_path)
    # Extract the text from each paragraph in the document
    verse = "\n".join([para.text for para in document.paragraphs])

    # Given Sanskrit text
    verse  = """
    त्‍वम॑ग्ने अ॒ग्ने॒ त्वम् त्‍वम॑ग्ने ।
    """
    # Split the verse into units
    units = split_verse(verse)

    with open("result.csv", "w+", encoding='utf-8') as f:
    # Write each segment to the file
      for segment in tqdm.tqdm(units):
            try:
                sandhi_result = merge_words_depth(segment)
                f.write(sandhi_result + "\n")
                f.flush() 
            except Exception as e:
                print("Error : ",e)
                print(segment)



def csv_processor(file_path, output_path, col_number):
    ##### From excel sheet ############
    # Load the .xlsx file
    # file_path = '/Users/pragunamanvi/Downloads/rjm2.xlsx'
    df = pd.read_excel(file_path)
    # Specify the column number (0-based index)
    column_number = col_number-1  # For example, 2 means the 3rd column

    # Define the string to append
    new_column_values = []
    with open("error.txt", "w+") as f:
        for index, row in tqdm.tqdm(df.iterrows(), total=len(df), desc="Processing Rows"):
            original_value = row.iloc[column_number]
            try:
                units = split_verse(original_value)
                assert len(units) == 1
                new_column_values.append(merge_words_depth(units[0]))
            except Exception as e:
                f.write(original_value + "\n")
                new_column_values.append(original_value + " -B-")
                f.flush() 

    # Add the new column to the DataFrame
    df['sandhi'] = new_column_values
    # Save the modified DataFrame to a new Excel file
    new_file_path = output_path
    df.to_csv(new_file_path, index=False)
    print(f"New file saved as: {new_file_path}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Write the first 100 rows of a DataFrame to a new Excel file.")

    parser.add_argument('--input_file', type=str, help="Path to the input Excel file", required=True)
    parser.add_argument('--output_path', nargs='?', type=str, help="Path to the output csv file", default="/Users/pragunamanvi/Downloads/jata.csv")
    parser.add_argument('--col_number', nargs='?', type=int, help="Column number for Jata (default 3)", default=4)

    args = parser.parse_args()
    csv_processor(args.input_file, args.output_path, args.col_number)
    print("done!!")


if __name__ == "__main__":
    main()
