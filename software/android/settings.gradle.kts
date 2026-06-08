pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}

rootProject.name = "Prediction"
include(":app")

// Composite build: pull in stock-market's :core library module
includeBuild("../../domains/finance/projects/stock-market/development/software/android") {
    dependencySubstitution {
        substitute(module("com.prediction:core")).using(project(":core"))
    }
}
