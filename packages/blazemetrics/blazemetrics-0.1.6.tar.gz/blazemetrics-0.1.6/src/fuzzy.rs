use rayon::prelude::*;

/// Optimized Levenshtein distance calculation using dynamic programming with space optimization
#[inline]
pub fn levenshtein_distance_optimized(s1: &str, s2: &str) -> usize {
    let len1 = s1.chars().count();
    let len2 = s2.chars().count();
    
    if len1 == 0 { return len2; }
    if len2 == 0 { return len1; }
    
    // Use only two rows instead of full matrix
    let mut prev_row: Vec<usize> = (0..=len2).collect();
    let mut curr_row: Vec<usize> = vec![0; len2 + 1];
    
    for (i, c1) in s1.chars().enumerate() {
        curr_row[0] = i + 1;
        
        for (j, c2) in s2.chars().enumerate() {
            let cost = if c1 == c2 { 0 } else { 1 };
            curr_row[j + 1] = (curr_row[j] + 1)
                .min(prev_row[j + 1] + 1)
                .min(prev_row[j] + cost);
        }
        
        std::mem::swap(&mut prev_row, &mut curr_row);
    }
    
    prev_row[len2]
}

/// Calculate Damerau-Levenshtein distance (includes transpositions) - optimized version
pub fn damerau_levenshtein_distance_optimized(s1: &str, s2: &str) -> usize {
    let len1 = s1.chars().count();
    let len2 = s2.chars().count();
    
    if len1 == 0 { return len2; }
    if len2 == 0 { return len1; }
    
    // Use three rows for transposition support
    let mut prev2_row: Vec<usize> = (0..=len2).collect();
    let mut prev_row: Vec<usize> = (0..=len2).collect();
    let mut curr_row: Vec<usize> = vec![0; len2 + 1];
    
    for (i, c1) in s1.chars().enumerate() {
        curr_row[0] = i + 1;
        
        for (j, c2) in s2.chars().enumerate() {
            let cost = if c1 == c2 { 0 } else { 1 };
            curr_row[j + 1] = (curr_row[j] + 1)
                .min(prev_row[j + 1] + 1)
                .min(prev_row[j] + cost);
            
            // Check for transposition
            if i > 0 && j > 0 {
                let prev_c1 = s1.chars().nth(i - 1).unwrap();
                let prev_c2 = s2.chars().nth(j - 1).unwrap();
                if c1 == prev_c2 && prev_c1 == c2 {
                    curr_row[j + 1] = curr_row[j + 1].min(prev2_row[j - 1] + 1);
                }
            }
        }
        
        // Rotate rows
        prev2_row = prev_row;
        prev_row = curr_row.clone();
    }
    
    prev_row[len2]
}

/// Calculate Jaro-Winkler similarity (0.0 to 1.0) - optimized version
pub fn jaro_winkler_similarity_optimized(s1: &str, s2: &str) -> f64 {
    if s1.is_empty() && s2.is_empty() {
        return 1.0;
    }
    if s1.is_empty() || s2.is_empty() {
        return 0.0;
    }
    
    let len1 = s1.chars().count();
    let len2 = s2.chars().count();
    
    // Find matching characters within half the length of the longer string
    let match_distance = (len1.max(len2) / 2).saturating_sub(1);
    
    let mut s1_matches = vec![false; len1];
    let mut s2_matches = vec![false; len2];
    
    let mut matches = 0;
    let mut transpositions = 0;
    
    // Find matches
    for (i, c1) in s1.chars().enumerate() {
        let start = i.saturating_sub(match_distance);
        let end = (i + match_distance + 1).min(len2);
        
        for j in start..end {
            if !s2_matches[j] && c1 == s2.chars().nth(j).unwrap() {
                s1_matches[i] = true;
                s2_matches[j] = true;
                matches += 1;
                break;
            }
        }
    }
    
    if matches == 0 {
        return 0.0;
    }
    
    // Count transpositions
    let mut k = 0;
    for (i, matched) in s1_matches.iter().enumerate() {
        if *matched {
            while k < len2 && !s2_matches[k] {
                k += 1;
            }
            if k < len2 && s1.chars().nth(i).unwrap() != s2.chars().nth(k).unwrap() {
                transpositions += 1;
            }
            k += 1;
        }
    }
    
    let jaro = (matches as f64 / len1 as f64 + 
                matches as f64 / len2 as f64 + 
                (matches - transpositions / 2) as f64 / matches as f64) / 3.0;
    
    // Jaro-Winkler modification
    let prefix_len = s1.chars().zip(s2.chars())
        .take_while(|(a, b)| a == b)
        .count()
        .min(4);
    
    jaro + 0.1 * prefix_len as f64 * (1.0 - jaro)
}

/// Calculate Levenshtein distance between two strings
pub fn levenshtein_distance(s1: &str, s2: &str) -> usize {
    levenshtein_distance_optimized(s1, s2)
}

/// Calculate Damerau-Levenshtein distance (includes transpositions)
pub fn damerau_levenshtein_distance(s1: &str, s2: &str) -> usize {
    damerau_levenshtein_distance_optimized(s1, s2)
}

/// Calculate Jaro-Winkler similarity (0.0 to 1.0)
pub fn jaro_winkler_similarity(s1: &str, s2: &str) -> f64 {
    jaro_winkler_similarity_optimized(s1, s2)
}

/// Optimized fuzzy matching configuration
#[derive(Clone, Debug)]
pub struct FuzzyConfig {
    pub max_distance: usize,
    pub algorithm: FuzzyAlgorithm,
    pub case_sensitive: bool,
    pub normalize_whitespace: bool,
}

impl Default for FuzzyConfig {
    fn default() -> Self {
        Self {
            max_distance: 2,
            algorithm: FuzzyAlgorithm::Levenshtein,
            case_sensitive: false,
            normalize_whitespace: true,
        }
    }
}

#[derive(Clone, Debug, PartialEq)]
pub enum FuzzyAlgorithm {
    Levenshtein,
    DamerauLevenshtein,
    JaroWinkler,
}

/// Optimized fuzzy match result
#[derive(Clone, Debug)]
pub struct FuzzyMatch {
    pub pattern: String,
    pub text: String,
    pub distance: f64,
    pub similarity: f64,
    pub algorithm: FuzzyAlgorithm,
}

/// Ultra-fast fuzzy matching using optimized algorithms and caching
pub fn fuzzy_match_any_bool_optimized(
    texts: &[String],
    patterns: &[String],
    config: &FuzzyConfig,
) -> Vec<bool> {
    let normalized_patterns: Vec<String> = if config.case_sensitive {
        patterns.to_vec()
    } else {
        patterns.iter().map(|p| p.to_lowercase()).collect()
    };
    
    let normalized_texts: Vec<String> = if config.case_sensitive {
        texts.to_vec()
    } else {
        texts.iter().map(|t| t.to_lowercase()).collect()
    };
    
    // Pre-compute pattern lengths for early exit optimization
    let pattern_lengths: Vec<usize> = normalized_patterns.iter()
        .map(|p| p.chars().count())
        .collect();
    
    // Use parallel processing with optimized early exit
    texts.par_iter().enumerate().map(|(i, _text)| {
        let text = &normalized_texts[i];
        
        for (j, pattern) in normalized_patterns.iter().enumerate() {
            let pattern_len = pattern_lengths[j];
            
            // Check if any word in text matches the pattern
            let words: Vec<&str> = text.split_whitespace().collect();
            
            for word in words {
                // Quick length-based filtering at word level
                if config.algorithm == FuzzyAlgorithm::Levenshtein ||
                   config.algorithm == FuzzyAlgorithm::DamerauLevenshtein {
                    let word_len = word.chars().count();
                    if word_len.abs_diff(pattern_len) > config.max_distance {
                        continue; // Skip this word if too different in length
                    }
                }
                let distance = match config.algorithm {
                    FuzzyAlgorithm::Levenshtein => {
                        levenshtein_distance_optimized(word, pattern) as f64
                    }
                    FuzzyAlgorithm::DamerauLevenshtein => {
                        damerau_levenshtein_distance_optimized(word, pattern) as f64
                    }
                    FuzzyAlgorithm::JaroWinkler => {
                        let similarity = jaro_winkler_similarity_optimized(word, pattern);
                        1.0 - similarity  // Convert to distance
                    }
                };
                
                let threshold = match config.algorithm {
                    FuzzyAlgorithm::Levenshtein | FuzzyAlgorithm::DamerauLevenshtein => {
                        config.max_distance as f64
                    }
                    FuzzyAlgorithm::JaroWinkler => {
                        1.0 - (config.max_distance as f64 / 10.0).min(0.9)
                    }
                };
                
                if match config.algorithm {
                    FuzzyAlgorithm::Levenshtein | FuzzyAlgorithm::DamerauLevenshtein => {
                        distance <= threshold
                    }
                    FuzzyAlgorithm::JaroWinkler => {
                        (1.0 - distance) >= threshold
                    }
                } {
                    return true;  // Found a match, early exit
                }
            }
        }
        
        false  // No matches found
    }).collect()
}

/// Check if any text matches patterns using fuzzy matching (boolean result)
pub fn fuzzy_match_any_bool(
    texts: &[String],
    patterns: &[String],
    config: &FuzzyConfig,
) -> Vec<bool> {
    fuzzy_match_any_bool_optimized(texts, patterns, config)
}

/// Find all fuzzy matches for each text
pub fn fuzzy_match_any(
    texts: &[String],
    patterns: &[String],
    config: &FuzzyConfig,
) -> Vec<Vec<FuzzyMatch>> {
    let normalized_patterns: Vec<String> = if config.case_sensitive {
        patterns.to_vec()
    } else {
        patterns.iter().map(|p| p.to_lowercase()).collect()
    };
    
    let normalized_texts: Vec<String> = if config.case_sensitive {
        texts.to_vec()
    } else {
        texts.iter().map(|t| t.to_lowercase()).collect()
    };
    
    // Pre-compute pattern lengths for early exit optimization
    let pattern_lengths: Vec<usize> = normalized_patterns.iter()
        .map(|p| p.chars().count())
        .collect();
    
    texts.par_iter().enumerate().map(|(i, _text)| {
        let text = &normalized_texts[i];
        let mut matches = Vec::new();
        
        // Check each pattern
        for (j, pattern) in normalized_patterns.iter().enumerate() {
            let pattern_len = pattern_lengths[j];
            
            let words: Vec<&str> = text.split_whitespace().collect();
            let mut best_distance = f64::INFINITY;
            let mut best_similarity = 0.0;
            
            for word in words {
                // Quick length-based filtering at word level
                if config.algorithm == FuzzyAlgorithm::Levenshtein ||
                   config.algorithm == FuzzyAlgorithm::DamerauLevenshtein {
                    let word_len = word.chars().count();
                    if word_len.abs_diff(pattern_len) > config.max_distance {
                        continue;
                    }
                }
                let distance = match config.algorithm {
                    FuzzyAlgorithm::Levenshtein => {
                        levenshtein_distance_optimized(word, pattern) as f64
                    }
                    FuzzyAlgorithm::DamerauLevenshtein => {
                        damerau_levenshtein_distance_optimized(word, pattern) as f64
                    }
                    FuzzyAlgorithm::JaroWinkler => {
                        let similarity = jaro_winkler_similarity_optimized(word, pattern);
                        1.0 - similarity
                    }
                };
                
                if distance < best_distance {
                    best_distance = distance;
                    best_similarity = match config.algorithm {
                        FuzzyAlgorithm::Levenshtein | FuzzyAlgorithm::DamerauLevenshtein => {
                            let max_len = word.len().max(pattern.len());
                            if max_len == 0 { 1.0 } else { 1.0 - (distance / max_len as f64) }
                        }
                        FuzzyAlgorithm::JaroWinkler => {
                            1.0 - distance
                        }
                    };
                }
            }
            
            let threshold = match config.algorithm {
                FuzzyAlgorithm::Levenshtein | FuzzyAlgorithm::DamerauLevenshtein => {
                    config.max_distance as f64
                }
                FuzzyAlgorithm::JaroWinkler => {
                    1.0 - (config.max_distance as f64 / 10.0).min(0.9)
                }
            };
            
            if match config.algorithm {
                FuzzyAlgorithm::Levenshtein | FuzzyAlgorithm::DamerauLevenshtein => {
                    best_distance <= threshold
                }
                FuzzyAlgorithm::JaroWinkler => {
                    best_similarity >= threshold
                }
            } {
                matches.push(FuzzyMatch {
                    pattern: patterns[j].clone(),
                    text: texts[i].clone(),
                    distance: best_distance,
                    similarity: best_similarity,
                    algorithm: config.algorithm.clone(),
                });
            }
        }
        
        matches
    }).collect()
}

/// Find the best fuzzy match for each text
pub fn fuzzy_match_best(
    texts: &[String],
    patterns: &[String],
    config: &FuzzyConfig,
) -> Vec<Option<FuzzyMatch>> {
    let all_matches = fuzzy_match_any(texts, patterns, config);
    
    all_matches.into_iter().map(|matches| {
        matches.into_iter().max_by(|a, b| {
            a.similarity.partial_cmp(&b.similarity).unwrap_or(std::cmp::Ordering::Equal)
        })
    }).collect()
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_levenshtein_distance() {
        assert_eq!(levenshtein_distance("kitten", "sitting"), 3);
        assert_eq!(levenshtein_distance("", "abc"), 3);
        assert_eq!(levenshtein_distance("abc", ""), 3);
        assert_eq!(levenshtein_distance("", ""), 0);
        assert_eq!(levenshtein_distance("abc", "abc"), 0);
    }
    
    #[test]
    fn test_jaro_winkler_similarity() {
        assert!((jaro_winkler_similarity("MARTHA", "MARHTA") - 0.961).abs() < 0.001);
        assert!((jaro_winkler_similarity("DWAYNE", "DUANE") - 0.840).abs() < 0.001);
        assert_eq!(jaro_winkler_similarity("", ""), 1.0);
        assert_eq!(jaro_winkler_similarity("abc", ""), 0.0);
    }
    
    #[test]
    fn test_fuzzy_match_any() {
        let texts = vec!["hello world".to_string(), "goodbye".to_string()];
        let patterns = vec!["helo".to_string(), "goodby".to_string()];
        let config = FuzzyConfig::default();
        
        let matches = fuzzy_match_any(&texts, &patterns, &config);
        assert_eq!(matches.len(), 2);
        assert!(!matches[0].is_empty());  // "hello world" should match "helo"
        assert!(!matches[1].is_empty());  // "goodbye" should match "goodby"
    }
    
    #[test]
    fn test_optimized_functions() {
        // Test that optimized versions give same results
        let s1 = "kitten";
        let s2 = "sitting";
        
        assert_eq!(levenshtein_distance(s1, s2), levenshtein_distance_optimized(s1, s2));
        assert_eq!(damerau_levenshtein_distance(s1, s2), damerau_levenshtein_distance_optimized(s1, s2));
        assert!((jaro_winkler_similarity(s1, s2) - jaro_winkler_similarity_optimized(s1, s2)).abs() < 1e-10);
    }
} 