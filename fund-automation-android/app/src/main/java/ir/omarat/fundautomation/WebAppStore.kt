package ir.omarat.fundautomation

import org.json.JSONArray
import org.json.JSONObject

/**
 * نوشتن درصد محاسبه‌شده در `localStorage` صفحات وب‌اپ داخل WebView.
 *
 * ⚠️ نکتهٔ حیاتی: برای صندوق ۴ دو دسته کلید موازی وجود دارد.
 *   • `mofid_atie_*`  → مصرف‌کننده: gold4/percent.html
 *   • `pension_*`     → مصرف‌کننده: gold4/calculator.html و دیدبان (monitor)
 * هر دو باید هم‌زمان نوشته شوند، وگرنه یک بخش عدد را می‌بیند و بخش دیگر نه.
 */
object WebAppStore {

    /** کلیدهای صندوق ۴ (آتیه مفید). */
    private const val ATIE_PREFIX = "mofid_atie_"
    private const val PENSION_BASE = "pension_baseNumber"
    private const val PENSION_HISTORY = "pension_history"
    private const val PENSION_PEAK = "pension_peakNumber"

    /** کلیدهای صندوق ۵ (سینرژی). */
    private const val SYNERGY_OBJECT = "energy_fund_synergy"
    private const val SYNERGY_BASE = "sinergy_baseNumber"
    private const val SYNERGY_HISTORY = "sinergy_history"
    private const val SYNERGY_PEAK = "sinergy_peakNumber"

    /**
     * کلیدهای کامل هر صندوق برای پشتیبان‌گیری/بازیابی.
     *
     * صندوق ۴ دو دستهٔ موازی دارد (`mofid_atie_*` و `pension_*`) و هر دو باید
     * پشتیبان شوند؛ وگرنه پس از بازیابی، یکی از بخش‌ها (calculator یا دیدبان)
     * دادهٔ قدیمی نشان می‌دهد.
     */
    val ATIE_KEYS = listOf(
        "mofid_atie_history", "mofid_atie_baseNumber", "mofid_atie_percents",
        "mofid_atie_trash", "mofid_atie_goal", "mofid_atie_highlightedStates",
        "mofid_atie_periodTarget", "mofid_atie_achievedPeriods", "mofid_atie_notes",
        PENSION_HISTORY, PENSION_BASE, PENSION_PEAK
    )

    val SYNERGY_KEYS = listOf(
        SYNERGY_OBJECT, SYNERGY_BASE, SYNERGY_HISTORY, SYNERGY_PEAK
    )

    /**
     * اسکریپت جاوااسکریپت برای ثبت یک درصد جدید در حافظهٔ وب‌اپ.
     *
     * @param fund         `"atie"` یا `"synergy"`
     * @param base         مقدار پایهٔ قبلی (ریال)
     * @param newValue     مقدار جدید (ریال)
     * @param percent      درصد با دو رقم اعشار
     * @param type         نوع تغییر (increase/recovering/decrease/neutral)
     * @param jalaliDate   تاریخ شمسی برای نمایش
     * @param timestampMs  زمان ثبت (میلی‌ثانیه)
     */
    fun buildInjectScript(
        fund: String,
        base: Long,
        newValue: Long,
        percent: Double,
        type: String,
        jalaliDate: String,
        timestampMs: Long
    ): String {
        val percentStr = String.format(java.util.Locale.US, "%.2f", percent)
        return if (fund == "synergy") {
            synergyScript(base, newValue, percentStr, type, jalaliDate, timestampMs)
        } else {
            atieScript(base, newValue, percentStr, type, jalaliDate, timestampMs)
        }
    }

    private fun atieScript(
        base: Long, newValue: Long, percent: String, type: String,
        jalaliDate: String, ts: Long
    ): String {
        val historyItem = JSONObject().apply {
            put("id", ts)
            put("base", formatNumber(base))
            put("new", formatNumber(newValue))
            put("percent", percent)
            put("type", type)
            put("rawBase", base.toDouble())
            put("rawNew", newValue.toDouble())
            put("timestamp", ts)
            put("persianDate", jalaliDate)
            put("source", "automation")
            put("auto", true)
        }
        val percentItem = JSONObject().apply {
            put("value", percent.toDouble())
            put("timestamp", ts)
            put("source", "automation")
            put("auto", true)
        }

        return """
        (function(){
          try {
            var P = "$ATIE_PREFIX";
            var ts = $ts;
            var newVal = $newValue;
            var historyItem = $historyItem;
            var percentItem = $percentItem;
            function hasRecord(key){
              try {
                var arr = JSON.parse(localStorage.getItem(key)) || [];
                for (var i=0;i<arr.length;i++){ if (arr[i] && arr[i].id === ts) return true; }
              } catch(e){}
              return false;
            }
            if (hasRecord(P + "history") || hasRecord("$PENSION_HISTORY")) return "SKIP";

            // --- تاریخچهٔ mofid_atie_* ---
            var hist = [];
            try { hist = JSON.parse(localStorage.getItem(P + "history")) || []; } catch(e){ hist = []; }
            if (!(hist instanceof Array)) hist = [];
            hist.push(historyItem);
            localStorage.setItem(P + "history", JSON.stringify(hist));

            // --- فهرست درصدهای mofid_atie_* ---
            var percents = [];
            try { percents = JSON.parse(localStorage.getItem(P + "percents")) || []; } catch(e){ percents = []; }
            if (!(percents instanceof Array)) percents = [];
            percents.push(percentItem);
            localStorage.setItem(P + "percents", JSON.stringify(percents));

            // --- پایهٔ mofid_atie_* ---
            localStorage.setItem(P + "baseNumber", String(newVal));

            // --- دستهٔ موازی pension_* (برای calculator و دیدبان) ---
            var pHist = [];
            try { pHist = JSON.parse(localStorage.getItem("$PENSION_HISTORY")) || []; } catch(e){ pHist = []; }
            if (!(pHist instanceof Array)) pHist = [];
            pHist.push(historyItem);
            localStorage.setItem("$PENSION_HISTORY", JSON.stringify(pHist));
            localStorage.setItem("$PENSION_BASE", String(newVal));

            localStorage.setItem("emarat_last_modified", String(ts));

            // ⚠️ حیاتی: gold4 روی `beforeunload` متصل به saveData() است و
            // saveData آرایهٔ «درون‌حافظه» را روی localStorage بازنویسی می‌کند.
            // اگر فقط localStorage را تزریق کنیم، هنگام بسته شدن WebView رکورد
            // ما پاک می‌شود. پس حافظهٔ درون‌صفحه را هم از localStorage بازخوانی
            // می‌کنیم تا saveData همان دادهٔ درست را بنویسد.
            try {
              if (typeof window.reloadLocalData === 'function') {
                window.reloadLocalData();
                if (typeof window.saveData === 'function') window.saveData();
              }
            } catch(e){}

            return "OK";
          } catch(err) { return "ERR:" + err.message; }
        })();
        """.trimIndent()
    }

    private fun synergyScript(
        base: Long, newValue: Long, percent: String, type: String,
        jalaliDate: String, ts: Long
    ): String {
        val historyItem = JSONObject().apply {
            put("id", ts)
            put("base", formatNumber(base))
            put("new", formatNumber(newValue))
            put("percent", percent)
            put("type", type)
            put("rawBase", base.toDouble())
            put("rawNew", newValue.toDouble())
            put("timestamp", ts)
            put("persianDate", jalaliDate)
            put("source", "automation")
            put("auto", true)
        }
        val percentItem = JSONObject().apply {
            put("value", percent.toDouble())
            put("timestamp", ts)
            put("source", "automation")
            put("auto", true)
        }

        return """
        (function(){
          try {
            var ts = $ts;
            var newVal = $newValue;
            var historyItem = $historyItem;
            var percentItem = $percentItem;
            function hasRecord(key){
              try {
                var arr = JSON.parse(localStorage.getItem(key)) || [];
                for (var i=0;i<arr.length;i++){ if (arr[i] && arr[i].id === ts) return true; }
              } catch(e){}
              return false;
            }
            var obj0 = {};
            try { obj0 = JSON.parse(localStorage.getItem("$SYNERGY_OBJECT")) || {}; } catch(e){ obj0 = {}; }
            if (hasRecord("$SYNERGY_HISTORY")) return "SKIP";
            if (obj0.history instanceof Array) {
              for (var j=0;j<obj0.history.length;j++){
                if (obj0.history[j] && obj0.history[j].id === ts) return "SKIP";
              }
            }

            // --- تاریخچهٔ sinergy_history ---
            var hist = [];
            try { hist = JSON.parse(localStorage.getItem("$SYNERGY_HISTORY")) || []; } catch(e){ hist = []; }
            if (!(hist instanceof Array)) hist = [];
            hist.push(historyItem);
            localStorage.setItem("$SYNERGY_HISTORY", JSON.stringify(hist));

            // --- پایهٔ سینرژی ---
            localStorage.setItem("$SYNERGY_BASE", String(newVal));

            // --- شیء کامل energy_fund_synergy ---
            var obj = obj0;
            if (!(obj.percents instanceof Array)) obj.percents = [];
            obj.percents.push(percentItem);
            obj.baseNumber = newVal;
            if (!(obj.history instanceof Array)) obj.history = [];
            obj.history.push(historyItem);
            localStorage.setItem("$SYNERGY_OBJECT", JSON.stringify(obj));

            localStorage.setItem("emarat_last_modified", String(ts));
            return "OK";
          } catch(err) { return "ERR:" + err.message; }
        })();
        """.trimIndent()
    }

    /** ساخت بدنهٔ بکاپ صندوق ۴ برای فایل gold4_backup.json. */
    fun buildAtieBackupPayload(percent: Double, base: Long, newValue: Long, ts: Long): String {
        val obj = JSONObject().apply {
            put("baseNumber", newValue)
            put("percents", JSONArray().put(percentRecord(percent, ts)))
            put("history", JSONArray().put(historyRecord(base, newValue, percent, ts)))
            put("trash", JSONArray())
            put("goal", JSONObject.NULL)
            put("highlightedStates", JSONObject())
            put("periodTarget", JSONObject.NULL)
            put("achievedPeriods", JSONArray())
            put("notes", JSONArray())
        }
        return obj.toString(2)
    }

    /** ساخت بدنهٔ بکاپ صندوق ۵ برای فایل gold5_backup.json. */
    fun buildSynergyBackupPayload(percent: Double, base: Long, newValue: Long, ts: Long): String {
        val obj = JSONObject().apply {
            put("baseNumber", newValue)
            put("percents", JSONArray().put(percentRecord(percent, ts)))
            put("history", JSONArray().put(historyRecord(base, newValue, percent, ts)))
            put("trash", JSONArray())
            put("goal", JSONObject.NULL)
        }
        return obj.toString(2)
    }

    private fun percentRecord(percent: Double, ts: Long): JSONObject = JSONObject().apply {
        put("value", percent)
        put("timestamp", ts)
        put("source", "automation")
        put("auto", true)
    }

    private fun historyRecord(base: Long, newValue: Long, percent: Double, ts: Long): JSONObject =
        JSONObject().apply {
            put("id", ts)
            put("base", formatNumber(base))
            put("new", formatNumber(newValue))
            put("percent", String.format(java.util.Locale.US, "%.2f", percent))
            put("rawBase", base.toDouble())
            put("rawNew", newValue.toDouble())
            put("timestamp", ts)
            put("source", "automation")
            put("auto", true)
        }

    private fun formatNumber(n: Long): String = String.format("%,d", n)
}
