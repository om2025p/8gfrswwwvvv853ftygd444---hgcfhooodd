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
            var base = $base, newVal = $newValue;
            var historyItem = $historyItem;
            var percentItem = $percentItem;

            // --- تاریخچهٔ mofid_atie_* ---
            var hist = [];
            try { hist = JSON.parse(localStorage.getItem(P + "history")) || []; } catch(e){ hist = []; }
            hist.push(historyItem);
            localStorage.setItem(P + "history", JSON.stringify(hist));

            // --- فهرست درصدهای mofid_atie_* ---
            var percents = [];
            try { percents = JSON.parse(localStorage.getItem(P + "percents")) || []; } catch(e){ percents = []; }
            percents.push(percentItem);
            localStorage.setItem(P + "percents", JSON.stringify(percents));

            // --- پایهٔ mofid_atie_* ---
            localStorage.setItem(P + "baseNumber", String(newVal));

            // --- دستهٔ موازی pension_* (برای calculator و دیدبان) ---
            var pHist = [];
            try { pHist = JSON.parse(localStorage.getItem("$PENSION_HISTORY")) || []; } catch(e){ pHist = []; }
            pHist.push(historyItem);
            localStorage.setItem("$PENSION_HISTORY", JSON.stringify(pHist));
            localStorage.setItem("$PENSION_BASE", String(newVal));

            localStorage.setItem("emarat_last_modified", String(ts));
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

            // --- تاریخچهٔ sinergy_history ---
            var hist = [];
            try { hist = JSON.parse(localStorage.getItem("$SYNERGY_HISTORY")) || []; } catch(e){ hist = []; }
            hist.push(historyItem);
            localStorage.setItem("$SYNERGY_HISTORY", JSON.stringify(hist));

            // --- پایهٔ سینرژی ---
            localStorage.setItem("$SYNERGY_BASE", String(newVal));

            // --- شیء کامل energy_fund_synergy ---
            var obj = {};
            try { obj = JSON.parse(localStorage.getItem("$SYNERGY_OBJECT")) || {}; } catch(e){ obj = {}; }
            var pList = obj.percents || [];
            pList.push(percentItem);
            obj.percents = pList;
            obj.baseNumber = newVal;
            var hList = obj.history || [];
            hList.push(historyItem);
            obj.history = hList;
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
            put("percents", JSONArray().put(JSONObject().apply {
                put("value", percent); put("timestamp", ts)
                put("source", "automation"); put("auto", true)
            }))
            put("history", JSONArray().put(JSONObject().apply {
                put("id", ts)
                put("base", formatNumber(base))
                put("new", formatNumber(newValue))
                put("percent", String.format(java.util.Locale.US, "%.2f", percent))
                put("rawBase", base.toDouble())
                put("rawNew", newValue.toDouble())
                put("timestamp", ts)
                put("source", "automation")
                put("auto", true)
            }))
            put("trash", JSONArray())
            put("goal", JSONObject.NULL)
            put("highlightedStates", JSONObject())
            put("periodTarget", JSONObject.NULL)
            put("achievedPeriods", JSONArray())
            put("notes", JSONArray())
        }
        return obj.toString(2)
    }

    private fun formatNumber(n: Long): String = String.format("%,d", n)
}
