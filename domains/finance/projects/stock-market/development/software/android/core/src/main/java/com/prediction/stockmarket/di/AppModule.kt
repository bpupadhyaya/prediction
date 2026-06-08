package com.prediction.stockmarket.di

import android.content.Context
import android.content.SharedPreferences
import androidx.room.Room
import com.google.gson.Gson
import com.prediction.stockmarket.data.database.*
import com.prediction.stockmarket.data.sync.MarketDataSourceManager
import com.prediction.stockmarket.data.sync.StooqFetcher
import com.prediction.stockmarket.data.sync.YahooFinanceFetcher
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
            .fallbackToDestructiveMigration()
            .build()

    @Provides fun provideStockDao(db: AppDatabase): StockDao = db.stockDao()
    @Provides fun providePriceDao(db: AppDatabase): PriceDao = db.priceDao()
    @Provides fun providePredictionDao(db: AppDatabase): PredictionDao = db.predictionDao()
    @Provides fun provideWatchlistDao(db: AppDatabase): WatchlistDao = db.watchlistDao()
    @Provides fun providePortfolioDao(db: AppDatabase): PortfolioDao = db.portfolioDao()

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
}
