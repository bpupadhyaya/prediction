package com.prediction.stockmarket.prediction

import kotlin.math.abs

/**
 * Perturbation-based "why this prediction" explainer.
 *
 * For each input feature, it replaces that feature with its training baseline and
 * measures how the CALIBRATED P(up) changes. A large positive delta means the
 * feature's actual value pushes the probability up relative to a neutral input;
 * a large negative delta means it pushes it down.
 */
object PredictionExplainer {

    data class FeatureContribution(
        val feature: String,
        val label: String,
        val value: Float,
        val delta: Double,
    ) {
        val pushesUp get() = delta >= 0
    }

    /**
     * @param features the 16-feature input (MOBILE_FEATURES order, newest-first derived).
     * @param horizon  UI horizon string (used only for labelling; scoring already encodes it).
     * @param score    closure returning the CALIBRATED P(up) for a given feature array.
     * @return contributions sorted by absolute impact, descending.
     */
    fun explain(
        features: FloatArray,
        horizon: String,
        score: (FloatArray) -> Double,
    ): List<FeatureContribution> {
        val base = score(features)
        val names = ModelMeta.featureNames
        val out = ArrayList<FeatureContribution>(features.size)
        for (i in features.indices) {
            val name = if (i < names.size) names[i] else "feature_$i"
            val perturbed = features.copyOf()
            perturbed[i] = ModelMeta.baseline(name)
            val delta = base - score(perturbed)
            out.add(
                FeatureContribution(
                    feature = name,
                    label = ModelMeta.label(name),
                    value = features[i],
                    delta = delta,
                )
            )
        }
        return out.sortedByDescending { abs(it.delta) }
    }

    /**
     * One plain-English sentence summarising the top drivers and whether each
     * supports or opposes the predicted [direction] ("UP"/"DOWN").
     */
    fun rationale(direction: String, contributions: List<FeatureContribution>): String {
        if (contributions.isEmpty()) return "No individual driver stands out for this prediction."
        val up = direction.equals("UP", ignoreCase = true)
        val top = contributions.take(3).filter { abs(it.delta) > 1e-6 }
        if (top.isEmpty()) return "No individual driver stands out for this prediction."

        val parts = top.map { c ->
            // A contribution supports the direction if it pushes the same way as the prediction.
            val supports = c.pushesUp == up
            val verb = if (supports) "supports" else "weighs against"
            "${c.label} $verb it"
        }
        val joined = when (parts.size) {
            1 -> parts[0]
            2 -> "${parts[0]} and ${parts[1]}"
            else -> "${parts[0]}, ${parts[1]}, and ${parts[2]}"
        }
        val dirWord = if (up) "higher" else "lower"
        return "The model leans $dirWord mainly because $joined."
    }
}
