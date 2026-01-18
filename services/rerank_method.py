
    def _rerank_combined_results(self, diagnoses: List[Dict], normalized_data: Dict) -> List[Dict]:
        """
        Intelligently rerank combined CSV + DDXPlus diagnoses.
        Downrank generic CSV results when specific DDXPlus results exist.
        
        Args:
            diagnoses: Combined list of diagnoses
            normalized_data: Patient data with atomic symptoms
        
        Returns:
            Reranked diagnoses
        """
        if not diagnoses:
            return diagnoses
        
        # Separate by source
        ddx_diagnoses = [d for d in diagnoses if d.get('evidence_type') == 'ddxplus-structured']
        csv_diagnoses = [d for d in diagnoses if d.get('evidence_type') == 'csv-symptom-match']
        medcase_diagnoses = [d for d in diagnoses if d.get('evidence_type') == 'medcase-llm-reasoning']
        
        # If DDXPlus has high-confidence results
        if ddx_diagnoses:
            ddx_max_score = max(d.get('match_score', 0) for d in ddx_diagnoses)
            
            if ddx_max_score > 50:
                logger.info(f"   DDXPlus has high-confidence results (max: {ddx_max_score:.1f}%)")
                
                # Downweight CSV results based on generic symptoms
                patient_symptoms = normalized_data.get("core_symptoms", [])
                for dx in csv_diagnoses:
                    matched_symptoms = dx.get('matched_symptoms', [])
                    
                    # If only 1-2 generic symptoms matched
                    if len(matched_symptoms) <= 2:
                        original_score = dx.get('match_score', 0)
                        dx['match_score'] = original_score * 0.4  # 60% reduction
                        logger.debug(f"   Downranked CSV '{dx['diagnosis']}': {original_score:.1f}% → {dx['match_score']:.1f}% (generic symptoms)")
                    elif len(matched_symptoms) <= 3:
                        original_score = dx.get('match_score', 0)
                        dx['match_score'] = original_score * 0.7  # 30% reduction
                        logger.debug(f"   Downranked CSV '{dx['diagnosis']}': {original_score:.1f}% → {dx['match_score']:.1f}% (limited symptoms)")
        
        # Recombine and sort
        all_diagnoses = ddx_diagnoses + csv_diagnoses + medcase_diagnoses
        all_diagnoses.sort(key=lambda x: x.get('match_score', 0), reverse=True)
        
        logger.info(f"   Reranking complete: {len(all_diagnoses)} diagnoses")
        return all_diagnoses
