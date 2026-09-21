package com.emarat.downloadshield;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import com.google.android.material.button.MaterialButton;

import java.util.List;

public class DownloadHistoryAdapter extends RecyclerView.Adapter<DownloadHistoryAdapter.ViewHolder> {

    public interface OnCopyErrorListener {
        void onCopyError(String errorLog);
    }

    private List<MainActivity.DownloadHistoryItem> historyList;
    private OnCopyErrorListener copyErrorListener;

    public DownloadHistoryAdapter(List<MainActivity.DownloadHistoryItem> historyList, OnCopyErrorListener listener) {
        this.historyList = historyList;
        this.copyErrorListener = listener;
    }

    public void updateData(List<MainActivity.DownloadHistoryItem> newList) {
        this.historyList = newList;
        notifyDataSetChanged();
    }

    @NonNull
    @Override
    public ViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext()).inflate(R.layout.item_download_history, parent, false);
        return new ViewHolder(view);
    }

    @Override
    public void onBindViewHolder(@NonNull ViewHolder holder, int position) {
        MainActivity.DownloadHistoryItem item = historyList.get(position);
        holder.tvTimestamp.setText("🕒 " + item.timestamp);
        holder.tvStatus.setText(item.statusText != null ? item.statusText : "در حال انجام");
        holder.tvLink.setText(item.link);

        if ("completed".equalsIgnoreCase(item.status)) {
            holder.tvStatus.setBackgroundColor(0xFFF0FDF4);
            holder.tvStatus.setTextColor(0xFF16A34A);
        } else if ("failed".equalsIgnoreCase(item.status)) {
            holder.tvStatus.setBackgroundColor(0xFFFEF2F2);
            holder.tvStatus.setTextColor(0xFFDC2626);
        } else {
            holder.tvStatus.setBackgroundColor(0xFFEFF6FF);
            holder.tvStatus.setTextColor(0xFF2563EB);
        }

        if (item.errorLog != null && !item.errorLog.isEmpty()) {
            holder.layoutErrorBox.setVisibility(View.VISIBLE);
            holder.tvErrorText.setText(item.errorLog);
            holder.btnCopyError.setOnClickListener(v -> {
                if (copyErrorListener != null) {
                    copyErrorListener.onCopyError(item.errorLog);
                }
            });
        } else {
            holder.layoutErrorBox.setVisibility(View.GONE);
        }
    }

    @Override
    public int getItemCount() {
        return historyList != null ? historyList.size() : 0;
    }

    public static class ViewHolder extends RecyclerView.ViewHolder {
        TextView tvTimestamp, tvStatus, tvLink, tvErrorText;
        LinearLayout layoutErrorBox;
        MaterialButton btnCopyError;

        public ViewHolder(@NonNull View itemView) {
            super(itemView);
            tvTimestamp = itemView.findViewById(R.id.tvItemTimestamp);
            tvStatus = itemView.findViewById(R.id.tvItemStatus);
            tvLink = itemView.findViewById(R.id.tvItemLink);
            tvErrorText = itemView.findViewById(R.id.tvErrorText);
            layoutErrorBox = itemView.findViewById(R.id.layoutErrorBox);
            btnCopyError = itemView.findViewById(R.id.btnCopyError);
        }
    }
}
