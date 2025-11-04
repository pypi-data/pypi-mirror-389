def doc():
    print(r"""
p1->text preprocessing
p2->sentiment analysis custom
p3->word2vec (skipgram && cbow)
p5->sentiment analysis priyank
p6->machine translation
p9->chatbot langchain
p10 -> RAG
""")
    
def p1():
    print(r"""
# =============================CELL===========================
import pandas as pd
import numpy as np
import re
import nltk
import spacy
import string

# =============================CELL===========================
trdf=pd.read_csv('train.csv', header='infer')

# =============================CELL===========================
trdf.info()

# =============================CELL===========================
trdf['lowered_text']=trdf['text'].str.lower()
print(trdf['lowered_text'].head(3))

# =============================CELL===========================
punctuations=string.punctuation
mapping = str.maketrans("","",punctuations)
trdf['lowered_text'].str.translate(mapping)

# =============================CELL===========================
from nltk.corpus import stopwords
print(len(stopwords.words('english')))
stopwords_eng=stopwords.words('english')

print(stopwords_eng)


# =============================CELL===========================
def remove_stopwords(in_str):
    new_str=''
    words=in_str.split()
    for tx in words:
        if tx not in stopwords_eng:
            new_str=new_str + tx + " "
    return new_str
trdf['lowered_text_stop_removed']=trdf["lowered_text"].apply(lambda x: remove_stopwords(x))
print(trdf["lowered_text_stop_removed"].head(10))

# =============================CELL===========================
from collections import Counter
counter=Counter()

for text in trdf["lowered_text_stop_removed"]:
    for word in text.split():
        counter[word]+=1

most_cmn_list=counter.most_common(10)
most_cmn_words_list=[]
for word, freq in most_cmn_list:
    most_cmn_words_list.append(word)
print(most_cmn_words_list)

# =============================CELL===========================
print(trdf['lowered_text_stop_removed'].head(10))
def remove_frequent(in_str):
    new_str=''
    for word in in_str.split():
        if word not in most_cmn_words_list:
            new_str=new_str + word + " "
    return new_str
trdf["lowered_text_stop_removed_freq_removed"]=trdf['lowered_text_stop_removed'].apply(lambda x: remove_frequent(x))
print(trdf["lowered_text_stop_removed_freq_removed"].head(10))


# =============================CELL===========================
most_rare_list=counter.most_common()[-10:]
most_rare_words=[]
for word, freq in most_rare_list:
    most_rare_words.append(word)

print(most_rare_words)

# =============================CELL===========================
def remove_rare(in_text):
    new_text=""
    for word in in_text.split():
        if word not in most_rare_words:
            new_text=new_text + word + " "
    return new_text
trdf["lowered_stop_freq_rare_removed"]=trdf["lowered_text_stop_removed_freq_removed"].apply(lambda x: remove_rare(x))
print(trdf["lowered_stop_freq_rare_removed"].head(10))

# =============================CELL===========================
from nltk.stem.porter import PorterStemmer
stemmer=PorterStemmer()
print(trdf["lowered_stop_freq_rare_removed"].head(5))

def do_stemming(in_str):
    new_str=""
    for word in in_str.split():
        new_str=new_str + stemmer.stem(word) + " "
    return new_str

trdf["Stemmed"]=trdf["lowered_stop_freq_rare_removed"].apply(lambda x: do_stemming(x))

print(trdf["Stemmed"].head(5))


# =============================CELL===========================
from nltk.stem import WordNetLemmatizer
lem=WordNetLemmatizer()

print(trdf["lowered_stop_freq_rare_removed"].head(5))

def do_lemmatizing(in_str):
    new_str=""
    for word in in_str.split():
        new_str=new_str + lem.lemmatize(word) + " "
    return new_str

trdf["Lemmatized"]=trdf["lowered_stop_freq_rare_removed"].apply(lambda x: do_lemmatizing(x))

print(trdf["Lemmatized"].head(5))

trdf["Lemmatized"].isnull().sum()

# =============================CELL===========================
def remove_emoji(in_str):
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"
                           u"\U0001F300-\U0001F5FF"
                           u"\U0001F680-\U0001F6FF"
                           u"\U0001F1E0-\U0001F1FF"
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE) 
    return emoji_pattern.sub(r'\\n', in_str)
remove_emoji("game is on 🔥🔥")

# =============================CELL===========================
#Removing URLs
def remove_urls(text):
    url_pattern = re.compile(r'https?://\S+|www\.\S+')

    return url_pattern.sub(r'', text)

text = "Ordinal and One-Hot Encodings for Categorical Data: https://machinelearningmastery.com/one-hot-encoding-for-categorical-data/"
remove_urls(text)

# =============================CELL===========================
from spellchecker import SpellChecker

spell = SpellChecker()

def correct_spellings(in_str):
    new_str = ""
    misspelled_words = spell.unknown(in_str.split())
    for word in in_str.split():
        if word in misspelled_words:
            new_str = new_str + spell.correction(word) + " "
        else:
            new_str = new_str + word + " "
    return new_str
        
text = "speling correctin"
correct_spellings(text)

# =============================CELL===========================



""")
def p2():
    print(r"""
# =============================CELL===========================
import torch
import torch.nn as nn
import pandas as pd
import numpy as np

# =============================CELL===========================
sentences = [
    "Hi I liked this movie I will rate this 9/10",
    "This movie was awesome",
    "I hate this movie and I will not see it again",
    "Absolutely fantastic film! Loved every moment.",
    "Terrible acting and poor direction",
    "A must-watch for all sci-fi lovers",
    "Waste of time. Not recommended",
    "Brilliant performances and stunning visuals",
    "The plot was dull and boring",
    "Enjoyed it a lot! Will watch again.",
    "Disappointed. Expected much more.",
    "Superb soundtrack and great story.",
    "I fell asleep. Too slow.",
    "What a masterpiece!",
    "Horrible. Never again.",
]
labels = [1, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]


# =============================CELL===========================
from collections import defaultdict
import torch


tokenized_sentences = [sentence.lower().split() for sentence in sentences]
print(tokenized_sentences)
print('\n'*10)
vocab = {"<PAD>": 0, "<UNK>": 1}
for sentence in tokenized_sentences:
    for word in sentence:
        if word not in vocab:
            vocab[word] = len(vocab)

print(vocab)
print('\n'*10)
indexed_sentences = [
    [vocab.get(word, vocab["<UNK>"]) for word in sentence]
    for sentence in tokenized_sentences
]

print(indexed_sentences)
print('\n'*10)
max_len = max(len(s) for s in indexed_sentences)
padded_sentences = [
    s + [vocab["<PAD>"]] * (max_len - len(s)) for s in indexed_sentences
]
print(padded_sentences)
print('\n'*10)
input_tensor = torch.tensor(padded_sentences)
print(input_tensor)
print('\n'*10)
label_tensor = torch.tensor(labels)


# =============================CELL===========================
import torch.nn as nn
import torch.nn.functional as F

class SentimentClassifier(nn.Module):
    def __init__(self, vocab_size, embedding_dim, hidden_dim):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim)
        self.fc1 = nn.Linear(embedding_dim * max_len, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, 1)

    def forward(self, x):
        x = self.embedding(x)
        x = x.view(x.size(0), -1)
        x = F.relu(self.fc1(x))
        x = torch.sigmoid(self.fc2(x))
        return x


# =============================CELL===========================
from torch.utils.data import TensorDataset, DataLoader


dataset = TensorDataset(input_tensor, label_tensor)
loader = DataLoader(dataset, batch_size=4, shuffle=True)


model = SentimentClassifier(vocab_size=len(vocab), embedding_dim=3, hidden_dim=64)
loss_fn = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=0.001)


for epoch in range(100):
    for xb, yb in loader:
        preds = model(xb).squeeze()
        loss = loss_fn(preds, yb.float())

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

    print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")


# =============================CELL===========================
def predict_sentiment(text):
    tokens = text.lower().split()
    idxs = [vocab.get(word, vocab["<UNK>"]) for word in tokens]
    padded = idxs + [vocab["<PAD>"]] * (max_len - len(idxs))
    inp = torch.tensor(padded).unsqueeze(0)  # Add batch dimension
    with torch.no_grad():
        pred = model(inp).item()
    return "Positive" if pred > 0.5 else "Negative"

print(predict_sentiment("What a wonderful movie!"))
print(predict_sentiment("This was a disaster."))


# =============================CELL===========================




""")
def p3():
    print(r"""
# =============================CELL===========================
!pip install torch==2.0.1 torchtext==0.15.2
!pip install 'portalocker>=2.0.0'

# =============================CELL===========================
from functools import partial
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch import optim

from torchtext import datasets
from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator

# =============================CELL===========================
if torch.cuda.is_available():
    device=torch.device(type='cuda',index=0)
else:
    device=torch.device(type='cpu',index=0)

# =============================CELL===========================
train_data=datasets.IMDB(split='train')

# =============================CELL===========================
eval_data=datasets.IMDB(split='test')

# =============================CELL===========================
mapped_train_data=[]
for label,review in train_data:
    mapped_train_data.append(review)

# =============================CELL===========================
mapped_eval_data=[]
for label,review in eval_data:
    mapped_eval_data.append(review)

# =============================CELL===========================
mapped_train_data[0] 

# =============================CELL===========================
print(type(mapped_train_data[0]))

# =============================CELL===========================
mapped_train_data[0:2]

# =============================CELL===========================
tokenizer = get_tokenizer("basic_english", language="en")


""
    Basic normalization for a line of text.
    Normalization includes
    - lowercasing
    - complete some basic text normalization for English words as follows:
        add spaces before and after '\''
        remove '\"',
        add spaces before and after '.'
        replace '<br \/>'with single space
        add spaces before and after ','
        add spaces before and after '('
        add spaces before and after ')'
        add spaces before and after '!'
        add spaces before and after '?'
        replace ';' with single space
        replace ':' with single space
        replace multiple spaces with single space

    Returns a list of tokens after splitting on whitespace.
    ""

# =============================CELL===========================
min_word_freq=20 
def build_vocab(mapped_train_data, tokenizer):        
    vocab = build_vocab_from_iterator(
        map(tokenizer, mapped_train_data),
        specials=["<unk>"],
        min_freq=min_word_freq
    )
    vocab.set_default_index(vocab["<unk>"])
    return vocab



# =============================CELL===========================
vocab=build_vocab(mapped_train_data,tokenizer)

# =============================CELL===========================
vocab_size=vocab.__len__()
print(vocab_size)

# =============================CELL===========================
window_size=4 
max_seq_len=256
max_norm=1
embed_dim=300
batch_size=16
text_pipeline = lambda x: vocab(tokenizer(x)) 


# =============================CELL===========================
sample=text_pipeline("Hello World")
print(sample)
print(type(sample))

# =============================CELL===========================
def collate_cbow(batch, text_pipeline):
    
     batch_input_words, batch_target_word = [], []
     
     for review in batch:
        
         review_tokens_ids = text_pipeline(review)
            
         if len(review_tokens_ids) < window_size * 2 + 1:
             continue
                
         if max_seq_len:
             review_tokens_ids = review_tokens_ids[:max_seq_len]
             
         for idx in range(len(review_tokens_ids) - window_size * 2):
             current_ids_sequence = review_tokens_ids[idx : (idx + window_size * 2 + 1)]
             target_word = current_ids_sequence.pop(window_size)
             input_words = current_ids_sequence
             batch_input_words.append(input_words)
             batch_target_word.append(target_word)
     
     batch_input_words = torch.tensor(batch_input_words, dtype=torch.long)
     batch_target_word = torch.tensor(batch_target_word, dtype=torch.long)
     
     return batch_input_words, batch_target_word

# =============================CELL===========================
def collate_skipgram(batch, text_pipeline):
    
    batch_input_word, batch_target_words = [], []
    
    for review in batch:
        review_tokens_ids = text_pipeline(review)

        if len(review_tokens_ids) < window_size * 2 + 1:
            continue

        if max_seq_len:
            review_tokens_ids = review_tokens_ids[:max_seq_len]

        for idx in range(len(review_tokens_ids) - window_size * 2):
            current_ids_sequence = review_tokens_ids[idx : (idx + window_size * 2 + 1)]
            input_word = current_ids_sequence.pop(window_size)
            target_words = current_ids_sequence

            for target_word in target_words:
                batch_input_word.append(input_word)
                batch_target_words.append(target_word)

    batch_input_word = torch.tensor(batch_input_word, dtype=torch.long)
    batch_target_words = torch.tensor(batch_target_words, dtype=torch.long)
    return batch_input_word, batch_target_words

# =============================CELL===========================
traindl_cbow = DataLoader(
        mapped_train_data,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=partial(collate_cbow,text_pipeline=text_pipeline)
    )

traindl_skipgram = DataLoader(
        mapped_train_data,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=partial(collate_skipgram,text_pipeline=text_pipeline)
    )

evaldl_cbow = DataLoader(
        mapped_eval_data,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=partial(collate_cbow,text_pipeline=text_pipeline)
    )

evaldl_skipgram = DataLoader(
        mapped_eval_data,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=partial(collate_skipgram,text_pipeline=text_pipeline)
    )

# =============================CELL===========================
class CBOW(nn.Module):
    
    def __init__(self, vocab_size):
        super().__init__()
        self.embeddings = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embed_dim,
            max_norm=max_norm
        )
        self.linear = nn.Linear(
            in_features=embed_dim,
            out_features=vocab_size,
        )

    def forward(self, x):
        x = self.embeddings(x)
        x = x.mean(axis=1)
        x = self.linear(x)
        return x

# =============================CELL===========================
class SkipGram(nn.Module):
    
    def __init__(self, vocab_size):
        super().__init__()
        self.embeddings = nn.Embedding(
            num_embeddings=vocab_size,
            embedding_dim=embed_dim,
            max_norm=max_norm
        )
        self.linear = nn.Linear(
            in_features=embed_dim,
            out_features=vocab_size,
        )

    def forward(self, x):
        x = self.embeddings(x)
        x = self.linear(x)
        return x

# =============================CELL===========================
def train_one_epoch(model,dataloader):
    model.train()
    running_loss = []

    for i, batch_data in enumerate(dataloader):
        inputs = batch_data[0].to(device)
        targets = batch_data[1].to(device)
        opt.zero_grad()
        outputs = model(inputs)
        loss = loss_fn(outputs, targets)
        loss.backward()
        opt.step()

        running_loss.append(loss.item())

    epoch_loss = np.mean(running_loss)
    print("Train Epoch Loss:",round(epoch_loss,3))
    loss_dict["train"].append(epoch_loss)

# =============================CELL===========================
def validate_one_epoch(model,dataloader):
    model.eval()
    running_loss = []

    with torch.no_grad():
        for i, batch_data in enumerate(dataloader, 1):
            inputs = batch_data[0].to(device)
            targets = batch_data[1].to(device)

            outputs = model(inputs)
            loss = loss_fn(outputs, targets)

            running_loss.append(loss.item())


    epoch_loss = np.mean(running_loss)
    print("Validation Epoch Loss:",round(epoch_loss,3))
    loss_dict["val"].append(epoch_loss)

# =============================CELL===========================
loss_fn=nn.CrossEntropyLoss()
n_epochs=5
loss_dict={}
loss_dict["train"]=[]
loss_dict["val"]=[]

choice=input("Enter cbow/skipgram:")
if choice=="cbow":
    model=CBOW(vocab_size).to(device)
    dataloader_train=traindl_cbow
    dataloader_val=evaldl_cbow
elif choice=="skipgram":
    model=SkipGram(vocab_size).to(device)
    dataloader_train=traindl_skipgram
    dataloader_val=evaldl_skipgram

opt=optim.Adam(params=model.parameters(),lr=0.001)

# =============================CELL===========================
for e in range(n_epochs):
    print("Epoch=",e+1)
    train_one_epoch(model,dataloader_train)
    validate_one_epoch(model,dataloader_val)

# =============================CELL===========================
for name,child in model.named_children():
    print(name,child)

# =============================CELL===========================
trimmed_model=model.embeddings
print(trimmed_model)

# =============================CELL===========================
print(vocab.get_itos()[0:100])
print(vocab.lookup_indices(["film","movie"]))

# =============================CELL===========================
emb1=trimmed_model(torch.tensor([vocab.lookup_indices(["film"])]).to(device))
emb2=trimmed_model(torch.tensor([vocab.lookup_indices(["movie"])]).to(device))
print(emb1.shape, emb2.shape)
cos=torch.nn.CosineSimilarity(dim=2)
print(cos(emb1,emb2))

emb1=trimmed_model(torch.tensor([vocab.lookup_indices(["his"])]).to(device))
emb2=trimmed_model(torch.tensor([vocab.lookup_indices(["from"])]).to(device))
print(cos(emb1,emb2))

emb1=trimmed_model(torch.tensor([vocab.lookup_indices(["he"])]).to(device))
emb2=trimmed_model(torch.tensor([vocab.lookup_indices(["were"])]).to(device))
print(cos(emb1,emb2))


""")
def p5():
    print(r"""
# =============================CELL===========================
!pip install torch==2.0.1 torchtext==0.15.2

# =============================CELL===========================
!pip install 'portalocker>=2.0.0'

# =============================CELL===========================
from functools import partial
import numpy as np

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torch import optim

from torchtext import datasets
from torchtext.data.functional import to_map_style_dataset
from torchtext.data.utils import get_tokenizer
from torchtext.vocab import build_vocab_from_iterator

# =============================CELL===========================
if torch.cuda.is_available():
    device=torch.device(type='cuda',index=0)
else:
    device=torch.device(type='cpu',index=0)

# =============================CELL===========================
train_data=datasets.IMDB(split='train') 

# =============================CELL===========================
eval_data=datasets.IMDB(split='test')

# =============================CELL===========================
mapped_train_data=to_map_style_dataset(train_data) 

# =============================CELL===========================
#check
print("Type of Mapped Train Data:",type(mapped_train_data))
print("0th data point",mapped_train_data[0])
print("Type of 0th data point",type(mapped_train_data[0]))
label,review=mapped_train_data[0]
print("Label=",label)
print("Review=",review)
print("Type of Label=",type(label))
print("Type of Review=",type(review))

print("iterating over 1 pair:")
for label,review in mapped_train_data:
    print(label)
    print(review)
    break

# =============================CELL===========================
mapped_eval_data=to_map_style_dataset(eval_data)

# =============================CELL===========================
tokenizer = get_tokenizer("basic_english", language="en")

# =============================CELL===========================
min_word_freq=2
def build_vocab(mapped_train_data, tokenizer):
    reviews = [review for label, review in mapped_train_data]
    vocab = build_vocab_from_iterator(
        map(tokenizer, reviews),
        specials=["<unk>","<eos>","<pad>"],
        min_freq=min_word_freq
    )
    vocab.set_default_index(vocab["<unk>"])
    return vocab

# =============================CELL===========================
vocab=build_vocab(mapped_train_data,tokenizer)

# =============================CELL===========================
vocab_size=vocab.__len__()
print(vocab_size)

# =============================CELL===========================
max_seq_len=256
max_norm=1
embed_dim=300
batch_size=16
text_pipeline = lambda x: vocab(tokenizer(x)) 


# =============================CELL===========================
sample=text_pipeline("Hello World")
print(sample)
print(type(sample))

# =============================CELL===========================
def collate_data(batch, text_pipeline):
    
     reviews, targets = [], []
     
     for label,review in batch:
        
         review_tokens_ids = text_pipeline(review)
                 
                
         if max_seq_len:
             review_tokens_ids = review_tokens_ids[:max_seq_len]
        
         review_tokens_ids.append(1)
         l=len(review_tokens_ids)
        
        
         x=[2]*257
         x[:l]=review_tokens_ids
         
         reviews.append(x)
         targets.append(label)
     
     reviews = torch.tensor(reviews, dtype=torch.long)
     targets = torch.tensor(targets, dtype=torch.long)
     
     return reviews, targets

# =============================CELL===========================
traindl = DataLoader(
        mapped_train_data,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=partial(collate_data,text_pipeline=text_pipeline)
    )


evaldl= DataLoader(
        mapped_eval_data,
        batch_size=batch_size,
        shuffle=True,
        collate_fn=partial(collate_data,text_pipeline=text_pipeline)
    )

# =============================CELL===========================
for i,(labels,reviews) in enumerate(traindl):
    print(labels.shape, reviews.shape)
    break

# =============================CELL===========================
print(vocab(["<unk>","<eos>","<pad>"]))

# =============================CELL===========================
class SentiNN(nn.Module):
    def __init__(self, input_size, embed_size, hidden_size):
        super().__init__()
        self.e=nn.Embedding(input_size, embed_size)
        self.dropout=nn.Dropout(0.2)
        self.rnn=nn.GRU(embed_size,hidden_size, batch_first=True)
        self.out=nn.Linear(in_features=hidden_size,out_features=2)
    
    def forward(self,x):
        x=self.e(x)
        x=self.dropout(x)
        outputs, hidden=self.rnn(x) 
        hidden.squeeze_(0) 
        logits=self.out(hidden)
        return logits

# =============================CELL===========================
embed_size=128
hidden_size=256

sentinn=SentiNN(vocab_size,embed_size,hidden_size).to(device) 

loss_fn=nn.CrossEntropyLoss(ignore_index=2).to(device)
lr=0.001
opt=optim.Adam(params=sentinn.parameters(), lr=lr)

# =============================CELL===========================
def train_one_epoch():
    sentinn.train()
    track_loss=0
    num_correct=0
    
    for i, (reviews_ids,sentiments) in enumerate(traindl):
        reviews_ids=reviews_ids.to(device)
        sentiments=sentiments.to(device)-1
        logits=sentinn(reviews_ids)
        loss=loss_fn(logits,sentiments)
        
        
        track_loss+=loss.item()
        num_correct+=(torch.argmax(logits,dim=1)==sentiments).type(torch.float).sum().item()
        
        running_loss=round(track_loss/(i+(reviews_ids.shape[0]/batch_size)),4)
        running_acc=round((num_correct/((i*batch_size+reviews_ids.shape[0])))*100,4)
        
        opt.zero_grad()
        loss.backward()
        opt.step()
        
        
    epoch_loss=running_loss
    epoch_acc=running_acc
    return epoch_loss, epoch_acc

# =============================CELL===========================
def eval_one_epoch():
    sentinn.eval()
    track_loss=0
    num_correct=0
        
    for i, (reviews_ids,sentiments) in enumerate(evaldl):
        
        reviews_ids=reviews_ids.to(device)
        sentiments=sentiments.to(device)-1
        logits=sentinn(reviews_ids)
                           
        loss=loss_fn(logits,sentiments)
        
        
        track_loss+=loss.item()
        num_correct+=(torch.argmax(logits,dim=1)==sentiments).type(torch.float).sum().item()
        
        running_loss=round(track_loss/(i+(reviews_ids.shape[0]/batch_size)),4)
        running_acc=round((num_correct/((i*batch_size+reviews_ids.shape[0])))*100,4)
        
        
        
        
    epoch_loss=running_loss
    epoch_acc=running_acc
    return epoch_loss, epoch_acc

# =============================CELL===========================
n_epochs=10

for e in range(n_epochs):
    print("Epoch=",e+1, sep="", end=", ")
    epoch_loss,epoch_acc=train_one_epoch()
    print("Train Loss=", epoch_loss, "Train Acc", epoch_acc)
    epoch_loss,epoch_acc=eval_one_epoch()
    print("Eval Loss=", epoch_loss, "Eval Acc", epoch_acc)


""")
def p6():
    print(r"""
# =============================CELL===========================
import torch
import torch.nn as nn
from torch import optim
from torch.utils.data import Dataset, DataLoader, random_split

from io import open
import unicodedata
import re

# =============================CELL===========================
if torch.cuda.is_available():
    device=torch.device(type='cuda', index=0)
else:
    device=torch.device(type='cpu', index=0)

# =============================CELL===========================
#unicode 2 ascii, remove non-letter characters, trim
def normalizeString(s): 
    sres=""
    for ch in unicodedata.normalize('NFD', s): 
        #Return the normal form form ('NFD') for the Unicode string s.
        if unicodedata.category(ch) != 'Mn':
            # The function in the first part returns the general 
            # category assigned to the character ch as string. 
            # "Mn' refers to Mark, Nonspacing
            sres+=ch
    sres = re.sub(r"([.!?])", r" \1", sres) 
    # inserts a space before any occurrence of ".", "!", or "?" in the string sres. 
    sres = re.sub(r"[^a-zA-Z!?]+", r" ", sres) 
    # this line of code replaces any sequence of characters in sres 
    # that are not letters (a-z or A-Z) or the punctuation marks 
    # "!" or "?" with a single space character.
    return sres.strip()

#create list of pairs (list of lists) (no filtering)
def createNormalizedPairs():
    initpairs=[]
    for pair in data:
        s1,s2=pair.split('\t')
        s1=normalizeString(s1.lower().strip())
        s2=normalizeString(s2.lower().strip())
        initpairs.append([s1,s2])
    #print(len(initpairs))
    return initpairs

#filter pairs
max_length = 10
def filterPairs(initpairs):
    #filtering conditions in addition to max_length
    eng_prefixes = (
        "i am ", "i m ",
        "he is", "he s ",
        "she is", "she s ",
        "you are", "you re ",
        "we are", "we re ",
        "they are", "they re "
    )

    pairs=[]
    for pair in initpairs:
        if len(pair[0].split(" ")) < max_length and len(pair[1].split(" ")) < max_length and pair[0].lower().startswith(eng_prefixes):
            pairs.append(pair)

    print("Number of pairs after filtering:", len(pairs))
    return pairs #list of lists

# =============================CELL===========================
class Vocab:
    def __init__(self, name):
        self.name=name
        self.word2index={'SOS':0, 'EOS':1}
        self.index2word={0:'SOS', 1:'EOS'}
        self.word2count={}
        self.nwords=2
    
    def buildVocab(self,s):
        for word in s.split(" "):
            if word not in self.word2index:
                self.word2index[word]=self.nwords
                self.index2word[self.nwords]=word
                self.word2count[word]=1
                self.nwords+=1
            else:
                self.word2count[word]+=1

# =============================CELL===========================
class Encoder(nn.Module):
    def __init__(self, input_size, embed_size, hidden_size, dropout_p=0.1):
        super().__init__()
        self.e=nn.Embedding(input_size, embed_size)
        self.dropout=nn.Dropout(dropout_p)
        self.gru=nn.GRU(embed_size,hidden_size, batch_first=True)
    
    def forward(self,x):
        x=self.e(x)
        x=self.dropout(x)
        outputs, hidden=self.gru(x)
        return outputs, hidden

# =============================CELL===========================
class Decoder(nn.Module):
    def __init__(self,output_size,embed_size,hidden_size):
        super().__init__()
        self.e=nn.Embedding(output_size,embed_size)
        self.relu=nn.ReLU()
        self.gru=nn.GRU(embed_size, hidden_size, batch_first=True)
        self.lin=nn.Linear(hidden_size,output_size)
        self.lsoftmax=nn.LogSoftmax(dim=-1)
    
    def forward(self,x,prev_hidden):
        x=self.e(x)
        x=self.relu(x)
        output,hidden=self.gru(x,prev_hidden)
        y=self.lin(output)
        y=self.lsoftmax(y)
        return y, hidden

# =============================CELL===========================
def get_input_ids(sentence,langobj):
    input_ids=[]
    for word in sentence.split(" "):
        input_ids.append(langobj.word2index[word])
    
    if langobj.name=='fre': #translation-direction sensitive
        input_ids.append(langobj.word2index['EOS'])
    else:
        input_ids.insert(0,langobj.word2index['SOS'])
        input_ids.append(langobj.word2index['EOS'])
    return torch.tensor(input_ids)

# =============================CELL===========================
class CustomDataset(Dataset):
    def __init__(self):
        super().__init__()
    
    def __len__(self):
        return length
    
    def __getitem__(self,idx):
        t=pairs[idx][0] #translation-direction sensitive
        s=pairs[idx][1] #translation-direction sensitive
        s_input_ids=torch.zeros(max_length+1, dtype=torch.int64)
        t_input_ids=torch.zeros(max_length+2, dtype=torch.int64)
        s_input_ids[:len(s.split(" "))+1]=get_input_ids(s,fre) #translation-direction sensitive
        t_input_ids[:len(t.split(" "))+2]=get_input_ids(t,eng) #translation-direction sensitive
        
        return s_input_ids, t_input_ids

# =============================CELL===========================
def train_one_epoch():
    encoder.train()
    decoder.train()
    track_loss=0
    
    for i, (s_ids,t_ids) in enumerate(train_dataloader):
        s_ids=s_ids.to(device)
        t_ids=t_ids.to(device)
        encoder_outputs, encoder_hidden=encoder(s_ids)
        decoder_hidden=encoder_hidden
        yhats, decoder_hidden = decoder(t_ids[:,0:-1],decoder_hidden)
                    
        gt=t_ids[:,1:]
        
        yhats_reshaped=yhats.view(-1,yhats.shape[-1])
        
        gt=gt.reshape(-1)
        
        
        loss=loss_fn(yhats_reshaped,gt)
        track_loss+=loss.item()
        
        opte.zero_grad()
        optd.zero_grad()
        
        loss.backward()
        
        opte.step()
        optd.step()
        
    return track_loss/len(train_dataloader)    

# =============================CELL===========================
def ids2Sentence(ids,vocab):
    sentence=""
    for id in ids.squeeze():
        if id==0:
            continue
        word=vocab.index2word[id.item()]
        sentence+=word + " "
        if id==1:  
            break
    return sentence

# =============================CELL===========================
#eval loop (written assuming batch_size=1)
def eval_one_epoch(e,n_epochs):
    encoder.eval()
    decoder.eval()
    track_loss=0
    with torch.no_grad():
        for i, (s_ids,t_ids) in enumerate(test_dataloader):
            s_ids=s_ids.to(device)
            t_ids=t_ids.to(device)
            encoder_outputs, encoder_hidden=encoder(s_ids)
            decoder_hidden=encoder_hidden #n_dim=3
            input_ids=t_ids[:,0]
            yhats=[]
            if e+1==n_epochs:
                pred_sentence=""
            for j in range(1,max_length+2): #j starts from 1
                probs, decoder_hidden = decoder(input_ids.unsqueeze(1),decoder_hidden)
                yhats.append(probs)
                _,input_ids=torch.topk(probs,1,dim=-1)
                input_ids=input_ids.squeeze(1,2) #still a tensor
                if e+1==n_epochs:
                    word=eng.index2word[input_ids.item()] #batch_size=1
                    pred_sentence+=word + " "
                if input_ids.item() == 1: #batch_size=1
                    break
                                
            if e+1==n_epochs:
                src_sentence=ids2Sentence(s_ids,fre) #translation-direction sensitive
                gt_sentence=ids2Sentence(t_ids[:,1:],eng) #translation-direction sensitive

                print("\n-----------------------------------")
                print("Source Sentence:",src_sentence)
                print("GT Sentence:",gt_sentence)
                print("Predicted Sentence:",pred_sentence)
            
            yhats_cat=torch.cat(yhats,dim=1)
            yhats_reshaped=yhats_cat.view(-1,yhats_cat.shape[-1])
            gt=t_ids[:,1:j+1]
            gt=gt.view(-1)
            

            loss=loss_fn(yhats_reshaped,gt)
            track_loss+=loss.item()
            
        if e+1==n_epochs:    
            print("-----------------------------------")
        return track_loss/len(test_dataloader)    

# =============================CELL===========================
#driver code

#read data
data=open("/kaggle/input/eng-fre-trans/eng-fra.txt").read().strip().split('\n')
print("Total number of pairs:",len(data))

#create pairs (create + normalize)
initpairs=createNormalizedPairs() #list of lists. Each inner list is a pair

#filter pairs
pairs=filterPairs(initpairs)
length=len(pairs)

#create Vocab objects for each language
eng=Vocab('eng')
fre=Vocab('fre')

#build the vocab
for pair in pairs:
    eng.buildVocab(pair[0])
    fre.buildVocab(pair[1])

#print vocab size
print("English Vocab Length:",eng.nwords)
print("French Vocab Length:",fre.nwords)    
    
dataset=CustomDataset()
train_dataset,test_dataset=random_split(dataset,[0.99,0.01])

batch_size=32
train_dataloader=DataLoader(dataset=train_dataset,batch_size=batch_size, shuffle=False)
test_dataloader=DataLoader(dataset=test_dataset,batch_size=1, shuffle=False)

    
embed_size=300
hidden_size=512

encoder=Encoder(fre.nwords,embed_size,hidden_size).to(device) #translation-direction sensitive
decoder=Decoder(eng.nwords,embed_size,hidden_size).to(device) #translation-direction sensitive

loss_fn=nn.NLLLoss(ignore_index=0).to(device)
lr=0.001
opte=optim.Adam(params=encoder.parameters(), lr=lr, weight_decay=0.001)
optd=optim.Adam(params=decoder.parameters(), lr=lr, weight_decay=0.001)

n_epochs=80

for e in range(n_epochs):
    print("Epoch=",e+1, sep="", end=", ")
    print("Train Loss=", round(train_one_epoch(),4), sep="", end=", ")
    print("Eval Loss=",round(eval_one_epoch(e,n_epochs),4), sep="")


""")
def p9():
    print(r"""
import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

os.environ["GROQ_API_KEY"] = "PLACEHOLDER"

llm = ChatGroq(
    model="groq/compound-mini",
    temperature=0.7,
    max_tokens=1024
)

_store = {}

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    ""Return or create chat history for a session.""
    if session_id not in _store:
        _store[session_id] = InMemoryChatMessageHistory()
    return _store[session_id]

conversation = RunnableWithMessageHistory(
    runnable=llm,
    get_session_history=get_session_history
)

def chat(session_id: str, user_input: str) -> str:
    human_msg = HumanMessage(content=user_input)
    ai_msg = conversation.invoke(
        human_msg,
        config={"configurable": {"session_id": session_id}}
    )
    return ai_msg.content

if _name_ == "_main_":
    print("Chatbot ready! Type 'quit' to exit.\n")
    session_id = "default"

    while True:
        user_message = input("You: ")
        if user_message.lower() in ["quit", "exit", "bye"]:
            print("Chatbot: Goodbye!")
            break

        response = chat(session_id, user_message)
        print(f"Chatbot: {response}\n")
""")
def p10():
    print(r"""
from langchain_community.document_loaders import TextLoader
# from langchain_community.text_splitter import RecursiveCharacterTextSplitter
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
import os
from langchain_groq import ChatGroq

# Load the text file
curdir = os.path.dirname(os.path.abspath(_file_))
filepath = os.path.join(curdir, "external", "1 - A Game of Thrones.txt")
pers_dir = os.path.join(curdir, "db4", "chroma_db1")

if not os.path.exists(pers_dir):
    print("Creating DB")

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File {filepath} does not exist")
    loader = TextLoader(file_path=filepath)
    doc = loader.load()
    print(f"Loaded {len(doc)} document(s)")
    print(f"First 500 characters of the document:\n{doc[0].page_content[:500]}")
    print(f"Metadata of the document:\n{doc[0].metadata}")
    # Split the document into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = text_splitter.split_documents(doc)
    print(f"Split into {len(chunks)} chunks")
    print(f"First chunk:\n{chunks[0].page_content}")
    # Create embeddings
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    # Create a Chroma vector store
    db = Chroma.from_documents(documents=chunks, embedding=embeddings, persist_directory=pers_dir)
    
else:
    print("DB exists. Using existing DB")

    # Load the existing Chroma vector store
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = Chroma(persist_directory=pers_dir, embedding_function=embeddings)

query = "Who is Eddard Stark?"

retriever = db.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 3, "score_threshold": 0.3})
docs = retriever.invoke(query)
print(f"Found {len(docs)} documents")
for i, doc in enumerate(docs):
    print(f"\nDocument {i+1}:\n{doc.page_content}\nMetadata: {doc.metadata}")

from dotenv import load_dotenv
import os
load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

model = ChatGroq(model="llama-3.3-70b-versatile", api_key=groq_api_key)

context = " ".join([doc.page_content for doc in docs])

response = model.invoke([
    {"role": "system", "content": "You are a helpful assistant that helps people find information. Use the context to answer the question."},
    {"role": "user", "content": f"Context: {context}\n\nQuestion: {query}"}
])


print(f"Response: {response.content}")
""")