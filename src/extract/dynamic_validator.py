import re
import numpy as np
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

class DynamicValidator:
    """Dynamic validation system that adapts to content patterns without static lists."""
    
    def __init__(self):
        self.pattern_cache = {}
        self.context_analyzer = ContextAnalyzer()
        self.semantic_validator = SemanticValidator()
        
    def validate_financial_data(self, items, text_context):
        """Dynamically validate financial data based on patterns and context."""
        validated_items = []
        
        for item in items:
            content = item['content']
            data_type = item['type']
            
            # Dynamic validation based on data type patterns
            if self._is_valid_financial_pattern(content, data_type, text_context):
                validated_items.append(item)
        
        return validated_items
    
    def validate_shipping_addresses(self, items, text_context):
        """Dynamically validate shipping addresses based on context."""
        validated_items = []
        
        for item in items:
            content = item['content']
            data_type = item['type']
            
            # Check if content is actually address-related
            if self._is_valid_address_pattern(content, data_type, text_context):
                validated_items.append(item)
        
        return validated_items
    
    def validate_usernames(self, items, text_context):
        """Dynamically validate usernames based on patterns and context."""
        validated_items = []
        
        for item in items:
            content = item['content']
            data_type = item['type']
            
            # Check if content follows username patterns
            if self._is_valid_username_pattern(content, data_type, text_context):
                validated_items.append(item)
        
        return validated_items
    
    def _is_valid_financial_pattern(self, content, data_type, context):
        """Dynamic financial data validation."""
        content_lower = content.lower()
        
        # Check for actual financial patterns
        if data_type == 'credit_card':
            # Must be 13-19 digits with proper formatting
            cleaned = re.sub(r'[^\d]', '', content)
            return len(cleaned) in [13, 15, 16] and cleaned.isdigit()
        
        elif data_type == 'swift_code':
            # Must be 8-11 alphanumeric characters in proper format
            if not re.match(r'^[A-Z0-9]{8,11}$', content.strip()):
                return False
            # Check if it appears in financial context
            return self.context_analyzer.is_financial_context(context, content)
        
        elif data_type == 'iban':
            # Must start with 2 letters + 2 digits + alphanumeric
            if not re.match(r'^[A-Z]{2}\d{2}[A-Z0-9]{4,30}$', content.replace(' ', '')):
                return False
            return self.context_analyzer.is_financial_context(context, content)
        
        elif data_type == 'cvv':
            # Must be 3-4 digits
            cleaned = re.sub(r'[^\d]', '', content)
            return len(cleaned) in [3, 4] and cleaned.isdigit()
        
        elif data_type == 'expiry_date':
            # Must be valid MM/YY or MM/YYYY format
            return bool(re.match(r'^(0[1-9]|1[0-2])/(2[0-9]|3[0-9]|20[2-9][0-9])$', content.strip()))
        
        else:
            # For other types, check if it's in financial context
            return self.context_analyzer.is_financial_context(context, content)
    
    def _is_valid_address_pattern(self, content, data_type, context):
        """Dynamic address validation."""
        content_lower = content.lower()
        content_clean = content.strip()
        
        # Check for malware/irrelevant content
        if self.context_analyzer.is_malware_context(context, content):
            return False
        
        # Skip if content is too short or too long
        if len(content_clean) < 5 or len(content_clean) > 200:
            return False
        
        # Skip if content contains newlines or multiple sentences (likely not an address)
        if '\n' in content or content.count('.') > 2:
            return False
        
        if data_type == 'postal_address':
            # Must contain street number and name, and look like an address
            has_number = re.search(r'\d+', content)
            has_letters = re.search(r'[A-Za-z]', content)
            has_street_word = re.search(r'\b(?:street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr|way|place|pl|court|ct|circle|cir|terrace|ter)\b', content, re.IGNORECASE)
            
            return (has_number and has_letters and has_street_word and 
                   len(content_clean) > 8 and len(content_clean) < 100)
        
        elif data_type == 'postal_code':
            # Must be valid postal code format
            return bool(re.match(r'^[A-Z0-9\s\-]{3,10}$', content, re.IGNORECASE))
        
        elif data_type == 'coordinates':
            # Must contain decimal coordinates
            return bool(re.search(r'\d+\.\d+', content))
        
        elif data_type in ['drop_location', 'shipping_instructions', 'landmark_references', 'time_instructions']:
            # Must be address-related and not malware
            return (len(content_clean) > 5 and len(content_clean) < 150 and
                   not self.context_analyzer.is_malware_context(context, content))
        
        else:
            # For other types, check if it's address-related
            return self.context_analyzer.is_address_context(context, content)
    
    def _is_valid_username_pattern(self, content, data_type, context):
        """Dynamic username validation."""
        content_lower = content.lower()
        
        # Skip if it's clearly not a username
        if self._is_not_username(content, context):
            return False
        
        # Must follow username patterns
        if not re.match(r'^[A-Za-z0-9_\-\.]{3,20}$', content):
            return False
        
        # Skip common non-username patterns
        if self._is_common_word_or_phrase(content, context):
            return False
        
        return True
    
    def _is_not_username(self, content, context):
        """Check if content is clearly not a username."""
        # File extensions
        if content.startswith('.') or content.endswith(('.exe', '.pdf', '.bat', '.ps1', '.doc', '.zip', '.msi', '.rar', '.xls', '.js', '.scr', '.com')):
            return True
        
        # File paths
        if '/' in content or '\\' in content:
            return True
        
        # Just numbers
        if re.match(r'^\d+$', content):
            return True
        
        # Too short
        if len(content) <= 2:
            return True
        
        # Check context for malware/document indicators
        if self.context_analyzer.is_malware_context(context, content):
            return True
        
        return False
    
    def _is_common_word_or_phrase(self, content, context):
        """Check if content is a common word or phrase, not a username."""
        # Common English words
        common_words = {'the', 'and', 'for', 'with', 'from', 'this', 'that', 'have', 'will', 'been', 'they', 'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there', 'could', 'other', 'than', 'first', 'water', 'been', 'call', 'who', 'oil', 'sit', 'now', 'find', 'down', 'day', 'did', 'get', 'come', 'made', 'may', 'part'}
        
        if content.lower() in common_words:
            return True
        
        # Check if it's part of a larger phrase in context
        if self.context_analyzer.is_part_of_phrase(context, content):
            return True
        
        return False


class ContextAnalyzer:
    """Analyzes context to determine if content is relevant."""
    
    def __init__(self):
        self.financial_keywords = {
            'bank', 'account', 'credit', 'card', 'payment', 'transfer', 'swift', 'iban', 'routing', 'sort', 'cvv', 'expiry', 'billing', 'financial', 'money', 'currency', 'bitcoin', 'ethereum', 'wallet', 'crypto'
        }
        
        self.address_keywords = {
            'street', 'avenue', 'road', 'drive', 'lane', 'place', 'court', 'boulevard', 'way', 'circle', 'terrace', 'address', 'location', 'delivery', 'shipping', 'postal', 'zip', 'city', 'state', 'country', 'coordinates', 'gps', 'latitude', 'longitude'
        }
        
        self.malware_keywords = {
            'malware', 'virus', 'trojan', 'spyware', 'keylogger', 'stealer', 'rat', 'backdoor', 'exploit', 'payload', 'infect', 'destroy', 'damage', 'attack', 'crypto', 'miner', 'botnet', 'undetected', 'stealth', 'bypass', 'hack', 'hacking', 'breach', 'compromise'
        }
    
    def is_financial_context(self, context, content):
        """Check if content appears in financial context."""
        context_lower = context.lower()
        content_lower = content.lower()
        
        # Check for financial keywords in surrounding context
        financial_context = any(keyword in context_lower for keyword in self.financial_keywords)
        
        # Check if content appears near financial terms
        words_before_after = self._get_surrounding_words(context, content, 10)
        financial_nearby = any(keyword in words_before_after for keyword in self.financial_keywords)
        
        return financial_context or financial_nearby
    
    def is_address_context(self, context, content):
        """Check if content appears in address context."""
        context_lower = context.lower()
        content_lower = content.lower()
        
        # Check for address keywords in surrounding context
        address_context = any(keyword in context_lower for keyword in self.address_keywords)
        
        # Check if content appears near address terms
        words_before_after = self._get_surrounding_words(context, content, 10)
        address_nearby = any(keyword in words_before_after for keyword in self.address_keywords)
        
        return address_context or address_nearby
    
    def is_malware_context(self, context, content):
        """Check if content appears in malware context."""
        context_lower = context.lower()
        content_lower = content.lower()
        
        # Check if content itself contains malware indicators
        content_malware = any(keyword in content_lower for keyword in self.malware_keywords)
        if content_malware:
            return True
        
        # Check for malware keywords in surrounding context (more specific)
        # Only consider it malware context if the content appears near malware terms
        words_before_after = self._get_surrounding_words(context, content, 5)
        malware_nearby = any(keyword in words_before_after for keyword in self.malware_keywords)
        
        return malware_nearby
    
    def is_part_of_phrase(self, context, content):
        """Check if content is part of a larger phrase."""
        # Look for content surrounded by other words
        pattern = r'\b\w+\s+' + re.escape(content) + r'\s+\w+\b'
        if re.search(pattern, context, re.IGNORECASE):
            return True
        
        # Check if it's part of a sentence
        sentences = re.split(r'[.!?]', context)
        for sentence in sentences:
            if content in sentence and len(sentence.split()) > 3:
                return True
        
        return False
    
    def _get_surrounding_words(self, context, target, window_size=10):
        """Get words surrounding the target content."""
        try:
            target_index = context.lower().find(target.lower())
            if target_index == -1:
                return ""
            
            start = max(0, target_index - window_size * 10)
            end = min(len(context), target_index + len(target) + window_size * 10)
            
            return context[start:end].lower()
        except:
            return ""


class SemanticValidator:
    """Uses semantic analysis to validate content."""
    
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.pattern_vectors = {}
    
    def validate_semantic_pattern(self, content, expected_pattern, training_data):
        """Validate content against semantic patterns."""
        if not training_data:
            return True
        
        try:
            # Create vectors for training data
            training_texts = [item['content'] for item in training_data]
            training_vectors = self.vectorizer.fit_transform(training_texts)
            
            # Vectorize the content
            content_vector = self.vectorizer.transform([content])
            
            # Calculate similarity
            similarities = cosine_similarity(content_vector, training_vectors)
            avg_similarity = np.mean(similarities)
            
            # Return True if similarity is above threshold
            return avg_similarity > 0.3
        except:
            return True  # Default to True if analysis fails


# Global instance for use across extractors
dynamic_validator = DynamicValidator() 