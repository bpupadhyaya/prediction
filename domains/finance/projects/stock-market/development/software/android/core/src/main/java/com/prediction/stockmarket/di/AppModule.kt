package com.prediction.stockmarket.di

import android.content.Context
import android.content.SharedPreferences
import androidx.room.Room
import com.google.gson.Gson
import com.prediction.stockmarket.data.database.*
import com.prediction.stockmarket.data.sync.MarketDataSourceManager
import com.prediction.stockmarket.data.sync.StooqFetcher
import com.prediction.stockmarket.data.sync.YahooFinanceFetcher
import com.prediction.stockmarket.prediction.LLMInferenceEngine
import com.prediction.stockmarket.videointelligence.VideoIntelligenceManager
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import java.util.concurrent.TimeUnit
import javax.inject.Singleton

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides @Singleton
    fun provideDatabase(@ApplicationContext ctx: Context): AppDatabase =
        Room.databaseBuilder(ctx, AppDatabase::class.java, "stock_prediction.db")
            .addMigrations(AppDatabase.MIGRATION_1_2, AppDatabase.MIGRATION_2_3)
            .build()

    @Provides fun provideStockDao(db: AppDatabase): StockDao = db.stockDao()
    @Provides fun providePriceDao(db: AppDatabase): PriceDao = db.priceDao()
    @Provides fun providePredictionDao(db: AppDatabase): PredictionDao = db.predictionDao()
    @Provides fun provideWatchlistDao(db: AppDatabase): WatchlistDao = db.watchlistDao()
    @Provides fun providePortfolioDao(db: AppDatabase): PortfolioDao = db.portfolioDao()

    // Video Intelligence DAOs
    @Provides fun provideVideoSourceDao(db: AppDatabase): VideoSourceDao = db.videoSourceDao()
    @Provides fun provideVideoSignalDao(db: AppDatabase): VideoSignalDao = db.videoSignalDao()
    @Provides fun provideChannelTrackDao(db: AppDatabase): ChannelTrackDao = db.channelTrackDao()

    // Track Record DAO
    @Provides fun provideTrackedPredictionDao(db: AppDatabase): TrackedPredictionDao = db.trackedPredictionDao()

    @Provides @Singleton
    fun provideVideoIntelligenceManager(
        @ApplicationContext ctx: Context,
        db: AppDatabase,
        okHttpClient: OkHttpClient,
        llmEngine: LLMInferenceEngine
    ): VideoIntelligenceManager = VideoIntelligenceManager(ctx, db, okHttpClient, llmEngine)

    @Provides @Singleton
    fun provideOkHttp(): OkHttpClient = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(60, TimeUnit.SECONDS)
        .build()

    @Provides @Singleton
    fun provideGson(): Gson = Gson()

    @Provides @Singleton
    fun provideSharedPreferences(@ApplicationContext ctx: Context): SharedPreferences =
        ctx.getSharedPreferences("prediction_prefs", Context.MODE_PRIVATE)

    @Provides @Singleton
    fun provideMarketDataSourceManager(prefs: SharedPreferences): MarketDataSourceManager =
        MarketDataSourceManager(prefs)

    @Provides @Singleton
    fun provideYahooFinanceFetcher(client: OkHttpClient): YahooFinanceFetcher =
        YahooFinanceFetcher(client)

    @Provides @Singleton
    fun provideStooqFetcher(client: OkHttpClient): StooqFetcher =
        StooqFetcher(client)

    @Provides
    @Singleton
    fun provideLLMInferenceEngine(@ApplicationContext context: Context): LLMInferenceEngine =
        LLMInferenceEngine(context)
}
