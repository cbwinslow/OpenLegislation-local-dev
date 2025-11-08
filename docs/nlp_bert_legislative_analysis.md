# NLP and BERT Applications for Legislative Analysis

## Overview

This guide provides comprehensive implementation of NLP and BERT-based models for legislative text analysis, including bias detection, sentiment analysis, and consistency assessment.

## Pre-trained Models for Legislative Analysis

### Political Bias Detection Models

#### Hugging Face Models
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline

# Political bias detection using DeBERTa
class PoliticalBiasDetector:
    def __init__(self):
        self.model_name = "SOUMYADEEPSAR/political_bias_deberta-mnli"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
        self.pipeline = pipeline(
            "text-classification",
            model=self.model,
            tokenizer=self.tokenizer,
            device=0 if torch.cuda.is_available() else -1
        )
    
    def detect_bias(self, text):
        """Detect political bias in legislative text"""
        result = self.pipeline(text)
        
        # Process results
        bias_scores = {
            'left_bias': result[0]['score'] if result[0]['label'] == 'LEFT' else 0.0,
            'right_bias': result[0]['score'] if result[0]['label'] == 'RIGHT' else 0.0,
            'neutral': result[0]['score'] if result[0]['label'] == 'NEUTRAL' else 0.0,
            'confidence': max([r['score'] for r in result])
        }
        
        return {
            'bias_classification': result[0]['label'],
            'bias_scores': bias_scores,
            'text_length': len(text),
            'processed_at': datetime.now().isoformat()
        }

# Advanced bias detection with Llama 3.2
class AdvancedBiasDetector:
    def __init__(self):
        self.model_name = "anish-ket/Llama-3.2-3B-Instruct-Political-Bias-Detection-FTM"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_name,
            torch_dtype=torch.float16,
            device_map='auto'
        )
    
    def analyze_bias_detailed(self, text):
        """Detailed bias analysis with reasoning"""
        prompt = f"""
        Analyze the following legislative text for political bias:
        
        Text: {text}
        
        Provide analysis on:
        1. Political leaning (left/center/right)
        2. Emotional tone
        3. Framing techniques
        4. Target audience
        5. Overall bias level (1-10)
        
        Format as JSON with detailed explanations.
        """
        
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
        outputs = self.model.generate(**inputs, max_new_tokens=512, temperature=0.1)
        
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return self.parse_bias_response(response)
```

### Sentiment Analysis for Legislative Text

#### Multi-dimensional Sentiment Analysis
```python
from transformers import pipeline
import nltk
from textblob import TextBlob

class LegislativeSentimentAnalyzer:
    def __init__(self):
        # Initialize multiple sentiment models
        self.bert_sentiment = pipeline(
            "sentiment-analysis",
            model="distilbert-base-uncased-finetuned-sst-2-english"
        )
        
        self.political_sentiment = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest"
        )
        
        self.finbert_sentiment = pipeline(
            "sentiment-analysis",
            model="ProsusAI/finbert"
        )
    
    def analyze_sentiment_multi_dimensional(self, text):
        """Analyze sentiment using multiple models"""
        # BERT sentiment
        bert_result = self.bert_sentiment(text)[0]
        
        # Political sentiment
        political_result = self.political_sentiment(text)[0]
        
        # Financial sentiment (for budget-related text)
        finbert_result = self.finbert_sentiment(text)[0]
        
        # TextBlob for additional metrics
        blob = TextBlob(text)
        
        return {
            'bert_sentiment': {
                'label': bert_result['label'],
                'score': bert_result['score']
            },
            'political_sentiment': {
                'label': political_result['label'],
                'score': political_result['score']
            },
            'financial_sentiment': {
                'label': finbert_result['label'],
                'score': finbert_result['score']
            },
            'textblob_metrics': {
                'polarity': blob.sentiment.polarity,
                'subjectivity': blob.sentiment.subjectivity
            },
            'combined_sentiment': self.combine_sentiments(
                bert_result, political_result, finbert_result, blob
            ),
            'text_metrics': {
                'word_count': len(text.split()),
                'sentence_count': len(nltk.sent_tokenize(text)),
                'readability': self.calculate_readability(text)
            }
        }
    
    def combine_sentiments(self, bert, political, finbert, blob):
        """Combine multiple sentiment scores"""
        # Weighted combination based on text type
        weights = {'bert': 0.4, 'political': 0.4, 'financial': 0.1, 'textblob': 0.1}
        
        sentiment_scores = {
            'positive': 0.0,
            'negative': 0.0,
            'neutral': 0.0
        }
        
        # Convert each model's output to standardized format
        for model_name, result in [('bert', bert), ('political', political), ('financial', finbert)]:
            label = result['label'].lower()
            score = result['score']
            weight = weights[model_name]
            
            if 'pos' in label:
                sentiment_scores['positive'] += score * weight
            elif 'neg' in label:
                sentiment_scores['negative'] += score * weight
            else:
                sentiment_scores['neutral'] += score * weight
        
        # Normalize scores
        total = sum(sentiment_scores.values())
        if total > 0:
            for key in sentiment_scores:
                sentiment_scores[key] /= total
        
        return sentiment_scores
```

### Topic Modeling for Legislative Content

#### BERTopic for Legislative Topic Discovery
```python
from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
import umap

class LegislativeTopicModeler:
    def __init__(self):
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.topic_model = BERTopic(
            embedding_model=self.embedding_model,
            umap_model=umap.UMAP(n_neighbors=15, n_components=5),
            min_topic_size=10,
            verbose=True
        )
    
    def discover_topics(self, documents, document_types=None):
        """Discover topics in legislative documents"""
        # Preprocess legislative text
        processed_docs = [self.preprocess_legislative_text(doc) for doc in documents]
        
        # Fit topic model
        topics, probs = self.topic_model.fit_transform(processed_docs)
        
        # Get topic information
        topic_info = self.topic_model.get_topic_info()
        
        # Enhance with legislative-specific metadata
        enhanced_topics = self.enhance_topic_metadata(topic_info, document_types)
        
        return {
            'topics': enhanced_topics,
            'document_topics': topics,
            'topic_probabilities': probs,
            'topic_hierarchy': self.build_topic_hierarchy(topic_info)
        }
    
    def preprocess_legislative_text(self, text):
        """Preprocess text for legislative analysis"""
        # Remove legislative boilerplate
        text = self.remove_boilerplate(text)
        
        # Extract key legislative terms
        terms = self.extract_legislative_terms(text)
        
        # Normalize terminology
        text = self.normalize_terminology(text, terms)
        
        return text
    
    def enhance_topic_metadata(self, topic_info, document_types):
        """Add legislative context to topics"""
        enhanced_topics = []
        
        for _, topic in topic_info.iterrows():
            # Identify topic type
            topic_type = self.classify_topic_type(topic['Name'])
            
            # Map to legislative categories
            legislative_category = self.map_to_legislative_category(topic['Name'])
            
            # Calculate political polarity
            polarity = self.calculate_topic_polarity(topic['Representation'])
            
            enhanced_topic = {
                'topic_id': topic['Topic'],
                'name': topic['Name'],
                'frequency': topic['Count'],
                'representative_docs': topic['Representative_Docs'],
                'topic_type': topic_type,
                'legislative_category': legislative_category,
                'political_polarity': polarity,
                'key_terms': self.extract_key_terms(topic['Representation'])
            }
            
            enhanced_topics.append(enhanced_topic)
        
        return enhanced_topics
```

## Custom Model Training

### Domain-Specific Fine-Tuning

#### Legislative Text Classification
```python
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import Dataset
import torch

class LegislativeTextClassifier:
    def __init__(self, base_model='bert-base-uncased'):
        self.tokenizer = AutoTokenizer.from_pretrained(base_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            base_model,
            num_labels=15  # 15 legislative categories
        )
        
        # Add special tokens for legislative terms
        special_tokens = ['[BILL]', '[AMENDMENT]', '[RESOLUTION]', '[ACT]']
        self.tokenizer.add_special_tokens({'additional_special_tokens': special_tokens})
        self.model.resize_token_embeddings(len(self.tokenizer))
    
    def prepare_training_data(self, raw_data):
        """Prepare legislative data for training"""
        # Convert to datasets format
        dataset = Dataset.from_dict({
            'text': [item['text'] for item in raw_data],
            'label': [item['category_id'] for item in raw_data]
        })
        
        # Tokenize
        def tokenize_function(examples):
            return self.tokenizer(
                examples['text'],
                padding='max_length',
                truncation=True,
                max_length=512,
                return_tensors='pt'
            )
        
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        # Split dataset
        train_test_split = tokenized_dataset.train_test_split(test_size=0.2)
        
        return train_test_split['train'], train_test_split['test']
    
    def fine_tune(self, train_data, eval_data, output_dir='./legislative_classifier'):
        """Fine-tune model on legislative data"""
        training_args = TrainingArguments(
            output_dir=output_dir,
            num_train_epochs=5,
            per_device_train_batch_size=16,
            per_device_eval_batch_size=16,
            evaluation_strategy='epoch',
            save_strategy='epoch',
            load_best_model_at_end=True,
            metric_for_best_model='f1',
            greater_is_better=True,
            warmup_steps=500,
            weight_decay=0.01,
            logging_dir='./logs',
            logging_steps=100
        )
        
        def compute_metrics(eval_pred):
            predictions, labels = eval_pred
            predictions = np.argmax(predictions, axis=1)
            
            precision = precision_score(labels, predictions, average='weighted')
            recall = recall_score(labels, predictions, average='weighted')
            f1 = f1_score(labels, predictions, average='weighted')
            
            return {
                'precision': precision,
                'recall': recall,
                'f1': f1
            }
        
        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=train_data,
            eval_dataset=eval_data,
            compute_metrics=compute_metrics
        )
        
        # Train model
        trainer.train()
        
        # Save model
        trainer.save_model(output_dir)
        self.tokenizer.save_pretrained(output_dir)
        
        return trainer
```

### Named Entity Recognition for Legislative Text

#### Custom NER for Legislative Entities
```python
from transformers import AutoTokenizer, AutoModelForTokenClassification
from transformers import pipeline
import spacy

class LegislativeNER:
    def __init__(self):
        # Load base NER model
        self.ner_pipeline = pipeline(
            "ner",
            model="dbmdz/bert-large-cased-finetuned-conll03-english",
            aggregation_strategy="simple"
        )
        
        # Load spaCy for additional processing
        self.nlp = spacy.load("en_core_web_sm")
        
        # Legislative entity types
        self.legislative_entities = {
            'PERSON': ['senator', 'representative', 'congressman', 'delegate'],
            'ORG': ['committee', 'subcommittee', 'agency', 'department'],
            'GPE': ['state', 'district', 'county', 'city'],
            'LAW': ['bill', 'act', 'resolution', 'amendment', 'statute'],
            'DATE': ['session', 'congress', 'term']
        }
    
    def extract_legislative_entities(self, text):
        """Extract legislative-specific entities"""
        # Standard NER
        standard_entities = self.ner_pipeline(text)
        
        # Legislative-specific entity extraction
        doc = self.nlp(text)
        legislative_entities = []
        
        for ent in doc.ents:
            if self.is_legislative_entity(ent):
                legislative_entities.append({
                    'text': ent.text,
                    'label': self.map_to_legislative_label(ent),
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'confidence': self.calculate_confidence(ent)
                })
        
        # Combine and deduplicate
        all_entities = standard_entities + legislative_entities
        unique_entities = self.deduplicate_entities(all_entities)
        
        return {
            'entities': unique_entities,
            'entity_counts': self.count_entity_types(unique_entities),
            'key_legislators': self.extract_key_legislators(unique_entities),
            'committees_mentioned': self.extract_committees(unique_entities),
            'legal_references': self.extract_legal_references(unique_entities)
        }
    
    def is_legislative_entity(self, entity):
        """Check if entity is legislative-specific"""
        entity_text = entity.text.lower()
        
        for entity_type, keywords in self.legislative_entities.items():
            if any(keyword in entity_text for keyword in keywords):
                return True
        
        return False
```

## Text Processing Pipeline

### End-to-End Legislative Text Processing
```python
class LegislativeTextProcessor:
    def __init__(self):
        self.bias_detector = PoliticalBiasDetector()
        self.sentiment_analyzer = LegislativeSentimentAnalyzer()
        self.topic_modeler = LegislativeTopicModeler()
        self.ner_extractor = LegislativeNER()
        self.classifier = LegislativeTextClassifier()
    
    def process_legislative_document(self, document):
        """Complete processing pipeline for legislative document"""
        results = {
            'document_id': document['id'],
            'title': document['title'],
            'content': document['content'],
            'processing_timestamp': datetime.now().isoformat()
        }
        
        # 1. Bias Analysis
        bias_analysis = self.bias_detector.detect_bias(document['content'])
        results['bias_analysis'] = bias_analysis
        
        # 2. Sentiment Analysis
        sentiment_analysis = self.sentiment_analyzer.analyze_sentiment_multi_dimensional(
            document['content']
        )
        results['sentiment_analysis'] = sentiment_analysis
        
        # 3. Topic Modeling
        if len(document['content']) > 100:  # Only for substantial content
            topic_analysis = self.topic_modeler.discover_topics([document['content']])
            results['topic_analysis'] = topic_analysis
        
        # 4. Named Entity Recognition
        ner_analysis = self.ner_extractor.extract_legislative_entities(document['content'])
        results['ner_analysis'] = ner_analysis
        
        # 5. Text Classification
        classification = self.classifier.classify(document['content'])
        results['classification'] = classification
        
        # 6. Quality Metrics
        results['quality_metrics'] = self.calculate_text_quality(document['content'])
        
        # 7. Legislative Complexity
        results['complexity_metrics'] = self.calculate_legislative_complexity(
            document['content']
        )
        
        return results
    
    def calculate_text_quality(self, text):
        """Calculate various text quality metrics"""
        return {
            'readability_score': self.calculate_readability(text),
            'lexical_diversity': self.calculate_lexical_diversity(text),
            'sentence_complexity': self.calculate_sentence_complexity(text),
            'formality_score': self.calculate_formality(text),
            'technical_density': self.calculate_technical_density(text)
        }
    
    def calculate_legislative_complexity(self, text):
        """Calculate legislative-specific complexity metrics"""
        return {
            'legal_terms_count': self.count_legal_terms(text),
            'cross_references_count': self.count_cross_references(text),
            'amendments_count': self.count_amendments(text),
            'conditions_count': self.count_conditions(text),
            'overall_complexity': self.calculate_overall_complexity(text)
        }
```

## Performance Optimization

### Batch Processing
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

class BatchTextProcessor:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or multiprocessing.cpu_count()
        self.processor = LegislativeTextProcessor()
    
    def process_documents_batch(self, documents, batch_size=32):
        """Process multiple documents efficiently"""
        results = []
        
        # Process in batches
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            
            # Parallel processing within batch
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                future_to_doc = {
                    executor.submit(self.processor.process_legislative_document, doc): doc
                    for doc in batch
                }
                
                batch_results = []
                for future in as_completed(future_to_doc):
                    doc = future_to_doc[future]
                    try:
                        result = future.result()
                        batch_results.append(result)
                    except Exception as e:
                        print(f"Error processing document {doc['id']}: {e}")
                        batch_results.append({'error': str(e), 'document_id': doc['id']})
            
            results.extend(batch_results)
        
        return results
```

### Caching and Memoization
```python
from functools import lru_cache
import pickle
import hashlib

class CachedTextProcessor:
    def __init__(self, cache_dir='./cache'):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        self.processor = LegislativeTextProcessor()
    
    def get_cache_key(self, text):
        """Generate cache key for text"""
        return hashlib.md5(text.encode()).hexdigest()
    
    def process_with_cache(self, document):
        """Process document with caching"""
        cache_key = self.get_cache_key(document['content'])
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        # Check cache
        if os.path.exists(cache_file):
            with open(cache_file, 'rb') as f:
                cached_result = pickle.load(f)
                # Add cache metadata
                cached_result['cached'] = True
                cached_result['cache_timestamp'] = os.path.getmtime(cache_file)
                return cached_result
        
        # Process and cache result
        result = self.processor.process_legislative_document(document)
        result['cached'] = False
        
        # Save to cache
        with open(cache_file, 'wb') as f:
            pickle.dump(result, f)
        
        return result
    
    @lru_cache(maxsize=1000)
    def cached_bias_detection(self, text):
        """Cached bias detection"""
        return self.processor.bias_detector.detect_bias(text)
```

## Integration with Vector Databases

### Embedding Generation and Storage
```python
class VectorizedTextProcessor:
    def __init__(self, vector_store):
        self.text_processor = LegislativeTextProcessor()
        self.vector_store = vector_store
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
    
    def process_and_store(self, document):
        """Process document and store embeddings"""
        # Process text
        results = self.text_processor.process_legislative_document(document)
        
        # Generate embeddings for different components
        embeddings = {}
        
        # Full text embedding
        embeddings['full_text'] = self.embedding_model.encode(document['content'])
        
        # Title embedding
        embeddings['title'] = self.embedding_model.encode(document['title'])
        
        # Topic-based embeddings
        if 'topic_analysis' in results:
            for topic in results['topic_analysis']['topics']:
                topic_text = topic['name'] + ' ' + ' '.join(topic['key_terms'])
                embeddings[f"topic_{topic['topic_id']}"] = self.embedding_model.encode(topic_text)
        
        # Entity-based embeddings
        if 'ner_analysis' in results:
            for entity in results['ner_analysis']['entities']:
                entity_text = entity['text']
                embeddings[f"entity_{entity['label']}_{hash(entity_text) % 1000}"] = \
                    self.embedding_model.encode(entity_text)
        
        # Store in vector database
        vector_id = self.vector_store.store_document_embeddings(
            document_id=document['id'],
            embeddings=embeddings,
            metadata=results
        )
        
        return {
            'document_id': document['id'],
            'vector_id': vector_id,
            'processing_results': results,
            'embedding_count': len(embeddings)
        }
```

This comprehensive guide provides implementation details for NLP and BERT applications in legislative analysis, covering bias detection, sentiment analysis, topic modeling, and custom model training.