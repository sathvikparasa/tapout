//
//  ChatTab.swift
//  TapOut
//
//  Global anonymous chat with AI content moderation.
//

import SwiftUI

// MARK: - ChatTab

struct ChatTab: View {
    @ObservedObject var viewModel: AppViewModel

    var body: some View {
        VStack(spacing: 0) {
            // Header
            VStack(alignment: .leading, spacing: 4) {
                (Text("Tap")
                    .foregroundColor(AppColors.textPrimary)
                + Text("Out")
                    .foregroundColor(AppColors.accent))
                    .appFont(size: 11, weight: .bold)

                Text("Chat")
                    .appFont(size: 30, weight: .heavy)
                    .foregroundColor(AppColors.textPrimary)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(.horizontal, 24)
            .padding(.top, 12)
            .padding(.bottom, 8)

            ZStack {
                AppColors.background.ignoresSafeArea()

                if viewModel.chatIsLoading && viewModel.chatMessages.isEmpty {
                    VStack {
                        Spacer()
                        ProgressView()
                            .tint(AppColors.accent)
                        Spacer()
                    }
                } else if viewModel.chatMessages.isEmpty {
                    ChatEmptyStateView()
                } else {
                    ScrollViewReader { proxy in
                        ScrollView {
                            VStack(spacing: 8) {
                                ForEach(viewModel.chatMessages) { message in
                                    ChatMessageRow(message: message)
                                        .id(message.id)
                                }
                            }
                            .padding(.horizontal, 16)
                            .padding(.top, 12)
                            .padding(.bottom, 8)
                        }
                        .onAppear {
                            scrollToBottom(proxy: proxy, animated: false)
                        }
                        .onChange(of: viewModel.chatMessages.count) { _, _ in
                            scrollToBottom(proxy: proxy, animated: true)
                        }
                    }
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)

            ChatInputBar(viewModel: viewModel)
        }
        .task {
            await viewModel.loadChatMessages()
            while !Task.isCancelled {
                try? await Task.sleep(nanoseconds: 5_000_000_000)
                if !Task.isCancelled {
                    await viewModel.loadChatMessages()
                }
            }
        }
        .alert("Message Blocked", isPresented: $viewModel.chatShowError) {
            Button("OK", role: .cancel) { viewModel.chatShowError = false }
        } message: {
            Text(viewModel.chatError ?? "Your message could not be sent.")
        }
    }

    private func scrollToBottom(proxy: ScrollViewProxy, animated: Bool) {
        guard let lastId = viewModel.chatMessages.last?.id else { return }
        if animated {
            withAnimation(.easeOut(duration: 0.2)) {
                proxy.scrollTo(lastId, anchor: .bottom)
            }
        } else {
            proxy.scrollTo(lastId, anchor: .bottom)
        }
    }
}
// MARK: - Message Row

private struct ChatMessageRow: View {
    let message: ChatMessage

    var body: some View {
        HStack(alignment: .bottom, spacing: 0) {
            VStack(alignment: .leading, spacing: 4) {
                Text(message.content)
                    .appFont(size: 15)
                    .foregroundColor(AppColors.textPrimary)
                    .fixedSize(horizontal: false, vertical: true)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(
                        RoundedRectangle(cornerRadius: 20)
                            .fill(Color(hex: "E9E9EB"))
                    )
                    .opacity(message.isPending ? 0.55 : 1.0)

                HStack(spacing: 4) {
                    if message.isPending {
                        ProgressView()
                            .scaleEffect(0.45)
                            .frame(width: 10, height: 10)
                            .tint(AppColors.textMuted)
                    }
                    Text(relativeTime)
                        .appFont(size: 11)
                        .foregroundColor(AppColors.textMuted)
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }

            Spacer(minLength: 64)
        }
    }

    private var relativeTime: String {
        let minutes = message.minutesAgo
        if minutes == 0 { return "Just now" }
        if minutes < 60 { return "\(minutes)m ago" }
        let hours = minutes / 60
        if hours < 24 { return "\(hours)h ago" }
        return "\(hours / 24)d ago"
    }
}

// MARK: - Empty State

private struct ChatEmptyStateView: View {
    var body: some View {
        VStack {
            Spacer()
            VStack(spacing: 16) {
                Image(systemName: "bubble.left.and.bubble.right")
                    .font(.system(size: 48, weight: .light))
                    .foregroundColor(AppColors.textMuted)

                VStack(spacing: 6) {
                    Text("No messages yet")
                        .appFont(size: 18, weight: .bold)
                        .foregroundColor(AppColors.textPrimary)

                    Text("Be the first to say something!")
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textSecondary)
                        .multilineTextAlignment(.center)
                }
            }
            .padding(40)
            Spacer()
        }
    }
}

// MARK: - Input Bar

private struct ChatInputBar: View {
    @ObservedObject var viewModel: AppViewModel
    @FocusState private var isInputFocused: Bool

    private let maxLength = 280

    private var inputIsEmpty: Bool {
        viewModel.chatInputText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    var body: some View {
        VStack(spacing: 0) {
            Rectangle()
                .fill(AppColors.border.opacity(0.5))
                .frame(height: 1)

            HStack(alignment: .bottom, spacing: 12) {
                VStack(alignment: .trailing, spacing: 4) {
                    TextField("Say something...", text: $viewModel.chatInputText, axis: .vertical)
                        .appFont(size: 14)
                        .foregroundColor(AppColors.textPrimary)
                        .lineLimit(1...4)
                        .focused($isInputFocused)
                        .onChange(of: viewModel.chatInputText) { _, newValue in
                            if newValue.count > maxLength {
                                viewModel.chatInputText = String(newValue.prefix(maxLength))
                            }
                        }

                    if viewModel.chatInputText.count > maxLength - 30 {
                        Text("\(maxLength - viewModel.chatInputText.count)")
                            .appFont(size: 10)
                            .foregroundColor(
                                viewModel.chatInputText.count >= maxLength
                                    ? AppColors.dangerBright
                                    : AppColors.textMuted
                            )
                    }
                }

                Button {
                    isInputFocused = false
                    Task { await viewModel.sendChatMessage() }
                } label: {
                    if viewModel.chatIsSending {
                        ProgressView()
                            .frame(width: 32, height: 32)
                            .tint(AppColors.accent)
                    } else {
                        Image(systemName: "arrow.up.circle.fill")
                            .font(.system(size: 24))
                            .foregroundColor(inputIsEmpty ? AppColors.textMuted : AppColors.accent)
                    }
                }
                .disabled(inputIsEmpty || viewModel.chatIsSending)
            }
            .padding(.horizontal, 16)
            .padding(.vertical, 12)
        }
        .background(
            AppColors.frosted
                .ignoresSafeArea(edges: .bottom)
        )
        .background(
            Rectangle()
                .fill(.ultraThinMaterial)
                .ignoresSafeArea(edges: .bottom)
        )
    }
}

#Preview {
    ChatTab(viewModel: AppViewModel())
}
