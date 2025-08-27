# Download fine-tuned model from Google Drive
LINK_ID="1Gp6nNbok3QGJY6Ckd_hx8btgyz4EMgW0"
OUTPUT_FILE="finetuned_latin_bert.tar"        

# Extract confirmation token and UUID (if required)
CONFIRM=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=$LINK_ID" -O- | sed -rn 's/.*name="confirm" value="([0-9A-Za-z_]+)".*/\1\n/p')
UUID=$(wget --quiet --save-cookies /tmp/cookies.txt --keep-session-cookies --no-check-certificate "https://docs.google.com/uc?export=download&id=$LINK_ID" -O- | sed -rn 's/.*name="uuid" value="([0-9A-Za-z_-]+)".*/\1\n/p')

# Download the file
wget --no-check-certificate --load-cookies /tmp/cookies.txt "https://drive.usercontent.google.com/download?export=download&id=$LINK_ID&confirm=$CONFIRM&uuid=$UUID" -O $OUTPUT_FILE && rm -f /tmp/cookies.txt

# Ensure the target directory exists
mkdir -p contextual_embeddings/latin-bert-huggingface-finetuned

# Move and extract the file
mv $OUTPUT_FILE contextual_embeddings/latin-bert-finetuned/
cd contextual_embeddings/latin-bert-finetuned
tar -xf $OUTPUT_FILE
rm $OUTPUT_FILE