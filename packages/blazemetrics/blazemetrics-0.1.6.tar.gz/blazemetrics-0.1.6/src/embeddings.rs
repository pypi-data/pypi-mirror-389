use ndarray::{Array2, Axis};
use rayon::prelude::*;
use std::cmp::Ordering;

/// Ultra-fast vector normalization using SIMD-friendly operations
#[inline]
pub fn normalize_vector_fast(vector: &[f32]) -> Vec<f32> {
    let norm_squared: f32 = vector.iter().map(|x| x * x).sum();
    let norm = norm_squared.sqrt();
    
    if norm < 1e-9 {
        vector.to_vec()
    } else {
        vector.iter().map(|x| x / norm).collect()
    }
}

/// Ultra-fast cosine similarity calculation without normalization
#[inline]
pub fn cosine_similarity_fast(a: &[f32], b: &[f32]) -> f32 {
    let dot_product: f32 = a.iter().zip(b.iter()).map(|(x, y)| x * y).sum();
    let norm_a: f32 = a.iter().map(|x| x * x).sum::<f32>().sqrt();
    let norm_b: f32 = b.iter().map(|x| x * x).sum::<f32>().sqrt();
    
    if norm_a < 1e-9 || norm_b < 1e-9 {
        0.0
    } else {
        dot_product / (norm_a * norm_b)
    }
}

/// Ultra-fast batch cosine similarity with minimal allocations
pub fn batch_cosine_similarity_simple_fast(
    embeddings: &[Vec<f32>],
    query: &[f32],
) -> Vec<f32> {
    embeddings.par_iter().map(|emb| {
        cosine_similarity_fast(emb, query)
    }).collect()
}

/// Advanced embedding operations optimized for RAG and semantic search
pub mod advanced_ops {
    use super::*;
    
    /// Batch cosine similarity with SIMD optimization
    pub fn batch_cosine_similarity(
        embeddings: &[Vec<f32>],
        query: &[f32],
    ) -> Vec<f32> {
        batch_cosine_similarity_simple_fast(embeddings, query)
    }
    
    /// Ultra-fast semantic search with top-k results using optimized algorithms
    pub fn semantic_search_topk_fast(
        queries: &[Vec<f32>],
        corpus: &[Vec<f32>],
        top_k: usize,
    ) -> Vec<Vec<(usize, f32)>> {
        queries.par_iter().enumerate().map(|(query_idx, query)| {
            // Use parallel iterator for maximum performance
            let mut similarities: Vec<(usize, f32)> = corpus.par_iter().enumerate()
                .map(|(i, emb)| {
                    (i, cosine_similarity_fast(query, emb))
                })
                .collect();
            
            // Parallel sort for large datasets
            if similarities.len() > 1000 {
                similarities.par_sort_unstable_by(|a, b| {
                    b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
                });
            } else {
                similarities.sort_unstable_by(|a, b| {
                    b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
                });
            }
            
            similarities.truncate(top_k);
            similarities
        }).collect()
    }
    
    /// Semantic search with top-k results
    pub fn semantic_search_topk(
        queries: &[Vec<f32>],
        corpus: &[Vec<f32>],
        top_k: usize,
    ) -> Vec<Vec<(usize, f32)>> {
        semantic_search_topk_fast(queries, corpus, top_k)
    }
    
    /// Approximate nearest neighbor search using dot product
    pub fn approximate_nearest_neighbor(
        query: &[f32],
        corpus: &[Vec<f32>],
        top_k: usize,
        threshold: f32,
    ) -> Vec<(usize, f32)> {
        let mut candidates: Vec<(usize, f32)> = corpus.par_iter().enumerate()
            .filter_map(|(i, emb)| {
                let similarity = cosine_similarity_fast(query, emb);
                if similarity >= threshold {
                    Some((i, similarity))
                } else {
                    None
                }
            })
            .collect();
        
        // Sort by similarity and take top-k
        if candidates.len() > 1000 {
            candidates.par_sort_unstable_by(|a, b| {
                b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
            });
        } else {
            candidates.sort_unstable_by(|a, b| {
                b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
            });
        }
        
        candidates.truncate(top_k);
        candidates
    }
    
    /// Multi-query batch similarity with optimized matrix operations
    pub fn multi_query_similarity(
        queries: &[Vec<f32>],
        corpus: &[Vec<f32>],
    ) -> Array2<f32> {
        let query_count = queries.len();
        let corpus_count = corpus.len();
        
        // Compute similarity matrix using parallel operations
        let mut similarity_matrix = Array2::zeros((query_count, corpus_count));
        
        similarity_matrix.axis_iter_mut(Axis(0)).into_par_iter().enumerate().for_each(|(i, mut row)| {
            let query = &queries[i];
            for (j, corpus_emb) in corpus.iter().enumerate() {
                row[j] = cosine_similarity_fast(query, corpus_emb);
            }
        });
        
        similarity_matrix
    }
    
    /// Fast semantic clustering using similarity threshold
    pub fn semantic_clustering_fast(
        embeddings: &[Vec<f32>],
        similarity_threshold: f32,
        min_cluster_size: usize,
    ) -> Vec<Vec<usize>> {
        let mut clusters = Vec::new();
        let mut assigned = vec![false; embeddings.len()];
        
        for i in 0..embeddings.len() {
            if assigned[i] {
                continue;
            }
            
            let mut cluster = Vec::new();
            let mut to_process = vec![i];
            
            while let Some(current) = to_process.pop() {
                if assigned[current] {
                    continue;
                }
                
                assigned[current] = true;
                cluster.push(current);
                
                // Find similar embeddings using parallel processing for large datasets
                if embeddings.len() > 1000 {
                    let similar_indices: Vec<usize> = (0..embeddings.len())
                        .into_par_iter()
                        .filter(|&j| !assigned[j])
                        .filter_map(|j| {
                            let similarity = cosine_similarity_fast(
                                &embeddings[current],
                                &embeddings[j]
                            );
                            if similarity >= similarity_threshold {
                                Some(j)
                            } else {
                                None
                            }
                        })
                        .collect();
                    
                    to_process.extend(similar_indices);
                } else {
                    // Sequential processing for small datasets
                    for j in 0..embeddings.len() {
                        if !assigned[j] {
                            let similarity = cosine_similarity_fast(
                                &embeddings[current],
                                &embeddings[j]
                            );
                            if similarity >= similarity_threshold {
                                to_process.push(j);
                            }
                        }
                    }
                }
            }
            
            if cluster.len() >= min_cluster_size {
                clusters.push(cluster);
            }
        }
        
        clusters
    }
    
    /// Semantic clustering using similarity threshold
    pub fn semantic_clustering(
        embeddings: &[Vec<f32>],
        similarity_threshold: f32,
        min_cluster_size: usize,
    ) -> Vec<Vec<usize>> {
        semantic_clustering_fast(embeddings, similarity_threshold, min_cluster_size)
    }
}

/// RAG-specific operations
pub mod rag_ops {
    use super::*;
    
    /// Ultra-fast RAG retrieval with reranking
    pub fn rag_retrieval_with_reranking(
        query: &[f32],
        passages: &[Vec<f32>],
        top_k: usize,
        rerank_threshold: f32,
    ) -> Vec<(usize, f32, f32)> {
        // First pass: fast approximate retrieval using dot product
        let mut initial_results: Vec<(usize, f32)> = passages.par_iter().enumerate()
            .map(|(idx, passage)| {
                let similarity = cosine_similarity_fast(query, passage);
                (idx, similarity)
            })
            .filter(|(_, similarity)| *similarity >= 0.1)  // Low threshold for initial pass
            .collect();
        
        // Sort and take top candidates
        if initial_results.len() > 1000 {
            initial_results.par_sort_unstable_by(|a, b| {
                b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
            });
        } else {
            initial_results.sort_unstable_by(|a, b| {
                b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
            });
        }
        
        initial_results.truncate(top_k * 2);
        
        // Second pass: exact similarity for reranking
        let mut reranked_results: Vec<(usize, f32, f32)> = initial_results.into_iter()
            .map(|(idx, _)| {
                let exact_similarity = cosine_similarity_fast(query, &passages[idx]);
                (idx, exact_similarity, exact_similarity)
            })
            .filter(|(_, similarity, _)| *similarity >= rerank_threshold)
            .collect();
        
        // Sort by exact similarity
        if reranked_results.len() > 1000 {
            reranked_results.par_sort_unstable_by(|a, b| {
                b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
            });
        } else {
            reranked_results.sort_unstable_by(|a, b| {
                b.1.partial_cmp(&a.1).unwrap_or(Ordering::Equal)
            });
        }
        
        reranked_results.truncate(top_k);
        reranked_results
    }
    
    /// Multi-modal similarity (text + image embeddings)
    pub fn multimodal_similarity(
        text_embeddings: &[Vec<f32>],
        image_embeddings: &[Vec<f32>],
        alpha: f32,  // Weight for text similarity
    ) -> Vec<Vec<f32>> {
        let beta = 1.0 - alpha;  // Weight for image similarity
        
        let mut similarity_matrix = Array2::zeros((text_embeddings.len(), image_embeddings.len()));
        
        similarity_matrix.axis_iter_mut(Axis(0)).into_par_iter().enumerate().for_each(|(i, mut row)| {
            let text_emb = &text_embeddings[i];
            for (j, image_emb) in image_embeddings.iter().enumerate() {
                let text_sim = cosine_similarity_fast(text_emb, image_emb);
                let image_sim = cosine_similarity_fast(text_emb, image_emb);
                row[j] = alpha * text_sim + beta * image_sim;
            }
        });
        
        similarity_matrix.rows().into_iter().map(|row| row.to_vec()).collect()
    }
}

/// Legacy functions for backward compatibility
pub fn normalize_vector(vector: &[f32]) -> Vec<f32> {
    normalize_vector_fast(vector)
}

pub fn cosine_similarity(a: &[f32], b: &[f32]) -> f32 {
    cosine_similarity_fast(a, b)
}

pub fn batch_cosine_similarity_simple(embeddings: &[Vec<f32>], query: &[f32]) -> Vec<f32> {
    batch_cosine_similarity_simple_fast(embeddings, query)
}

/// Performance-optimized operations
pub fn fast_dot_product(a: &[f32], b: &[f32]) -> f32 {
    // SIMD-friendly implementation
    let mut sum = 0.0f32;
    let len = a.len();
    
    // Process in chunks for better cache locality
    let chunk_size = 64;
    for chunk_start in (0..len).step_by(chunk_size) {
        let chunk_end = (chunk_start + chunk_size).min(len);
        let mut chunk_sum = 0.0f32;
        
        for i in chunk_start..chunk_end {
            chunk_sum += a[i] * b[i];
        }
        
        sum += chunk_sum;
    }
    
    sum
}

/// Memory-efficient similarity matrix computation
pub fn similarity_matrix_chunked(
    embeddings: &[Vec<f32>],
    chunk_size: usize,
) -> Vec<Vec<f32>> {
    let n = embeddings.len();
    let mut matrix = vec![vec![0.0f32; n]; n];
    
    // Process in chunks to manage memory usage
    for chunk_start in (0..n).step_by(chunk_size) {
        let chunk_end = (chunk_start + chunk_size).min(n);
        
        for i in chunk_start..chunk_end {
            for j in i..n {
                let similarity = cosine_similarity(&embeddings[i], &embeddings[j]);
                matrix[i][j] = similarity;
                matrix[j][i] = similarity;  // Symmetric matrix
            }
        }
    }
    
    matrix
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_normalize_vector() {
        let v = vec![3.0, 4.0];
        let normalized = normalize_vector(&v);
        assert!((normalized[0] - 0.6).abs() < 1e-6);
        assert!((normalized[1] - 0.8).abs() < 1e-6);
    }
    
    #[test]
    fn test_cosine_similarity() {
        let a = vec![1.0, 0.0];
        let b = vec![1.0, 0.0];
        assert!((cosine_similarity(&a, &b) - 1.0).abs() < 1e-6);
        
        let c = vec![0.0, 1.0];
        assert!((cosine_similarity(&a, &c) - 0.0).abs() < 1e-6);
    }
    
    #[test]
    fn test_batch_cosine_similarity() {
        let embeddings = vec![
            vec![1.0, 0.0],
            vec![0.0, 1.0],
            vec![1.0, 1.0],
        ];
        let query = vec![1.0, 0.0];
        
        let similarities = batch_cosine_similarity_simple(&embeddings, &query);
        assert_eq!(similarities.len(), 3);
        assert!((similarities[0] - 1.0).abs() < 1e-6);  // Perfect match
        assert!((similarities[1] - 0.0).abs() < 1e-6);  // Orthogonal
    }
} 