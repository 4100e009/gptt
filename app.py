from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
from linebot.models import ImageSendMessage

import matplotlib.pyplot as plt
import networkx as nx
import pyimgur
from io import BytesIO
import tempfile

def draw_straight_angle_edges(G, pos, ax):
    for edge in G.edges():
        start_pos = pos[edge[0]]
        end_pos = pos[edge[1]]
        mid_point = (end_pos[0], start_pos[1])  # 計算轉折點
        # Draw horizontal line from start to mid_point
        ax.plot([start_pos[0], mid_point[0]], [start_pos[1], mid_point[1]], 'k-', lw=1)
        # Draw vertical line from mid_point to end
        ax.plot([mid_point[0], end_pos[0]], [mid_point[1], end_pos[1]], 'k-', lw=1)
def generate_bracket_layout(num_participants, vertical_spacing=100):
    G = nx.DiGraph()
    rounds = num_participants.bit_length() - 1

    node_positions = {}
    for i in range(num_participants):
        node_positions[f'Player {i}'] = (0, i * vertical_spacing)

    current_nodes = list(node_positions.keys())
    spacing_factor = vertical_spacing  # 初始化間距因子
    for r in range(1, rounds + 1):
        next_nodes = []
        spacing_factor *= 8  # 每一輪加倍間距因子
        for i in range(0, len(current_nodes), 2):
            winner_node = f'Winner_R{r}_N{i//2}'
            G.add_node(winner_node)
            G.add_edge(current_nodes[i], winner_node)
            if i + 1 < len(current_nodes):
                G.add_edge(current_nodes[i+1], winner_node)

            # 計算勝者節點位置，並考慮間距因子
            y_pos = (node_positions[current_nodes[i]][1] + node_positions[current_nodes[i+1]][1]) / 2
            node_positions[winner_node] = (r, y_pos)
            next_nodes.append(winner_node)
        current_nodes = next_nodes

    pos = {node: (round_num, -y_pos) for node, (round_num, y_pos) in node_positions.items()}
    return G, pos

def upload_to_imgur(client_id, fig, title):
    with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmpfile:
        fig.savefig(tmpfile.name, format='png')
        im = pyimgur.Imgur(client_id)
        uploaded_image = im.upload_image(tmpfile.name, title=title)
    return uploaded_image.link

app = Flask(__name__)

line_bot_api = LineBotApi('coO4LWavHe99D01z1DuMbtygRQxo4/syXYPxjjUXr1+wvDHoGIbIv3UnnBZNJz51KdQq1YTKveOjT//Q2zOHZsTHe/i9e4lM8a4sfmv0Yy3whWUilp2R7ROCMrDGKBBgi+Hgy/QdAN8oe8kGcQ4FawdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('807708ddbeeb027e51e2c39033b75d5c')

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    # 解析用戶發送的消息，例如參與者數量
    try:
        num_participants = int(event.message.text)
        G, pos = generate_bracket_layout(num_participants, vertical_spacing=200)
        fig, ax = plt.subplots(figsize=(10, 5))
        # 繪製每個節點
        for node, (x, y) in pos.items():
            ax.text(x, y, node, fontsize=8, ha='center', va='center',
                    bbox=dict(facecolor='lightblue', edgecolor='black', boxstyle='round,pad=0.3'))

        # 繪製邊
        draw_straight_angle_edges(G, pos, ax)

        plt.axis('off')
        plt.tight_layout()
        imgur_link = upload_to_imgur('573b912b802db62', fig, 'Tournament Bracket')
        reply_message = ImageSendMessage(
            original_content_url=imgur_link,
            preview_image_url=imgur_link
        )
    except ValueError:
        reply_message = TextSendMessage(text='Please send a valid number.')

    line_bot_api.reply_message(event.reply_token, reply_message)
if __name__ == "__main__":
    app.run()
