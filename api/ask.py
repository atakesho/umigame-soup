import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler

API_URL = "https://api.typesafe.ai/v1/systemone"

PUZZLES = [
    {
        "title": "ウミガメのスープ",
        "story": "男はレストランでウミガメのスープを注文し、一口飲むと店を出て自殺した。なぜ?",
        "truth": (
            "男は昔、船が遭難して仲間と漂流していた。飢えの中で仲間が「ウミガメのスープだ」と"
            "言って肉のスープを飲ませてくれた。実は死んだ別の仲間の肉だった。"
            "今日レストランで本物のウミガメのスープを飲み、味が違うことであの時の真実に気づき、"
            "絶望して自殺した。"
        ),
    },
    {
        "title": "エレベーター",
        "story": "男は毎朝10階の自宅からエレベーターで1階に降りる。帰りは7階で降りて階段で10階まで上る。雨の日だけは10階まで乗る。なぜ?",
        "truth": (
            "男は背が低く、エレベーターのボタンは7階までしか手が届かない。"
            "雨の日は傘を持っているので、傘の先で10階のボタンを押せる。"
        ),
    },
    {
        "title": "砂漠の男",
        "story": "砂漠の真ん中で男が裸で死んでいた。手には折れたマッチ棒。周りに足跡はない。何があった?",
        "truth": (
            "男は熱気球に乗っていた仲間と一緒に飛んでいた。気球が高度を失い、誰かが降りる必要があった。"
            "マッチ棒でくじを引き、短いマッチを引いた男が服を捨てて重さを減らした後、"
            "それでも足りず自ら飛び降りた。"
        ),
    },
]

LABELS = {"yes": "はい", "no": "いいえ", "irrelevant": "関係ありません"}


def jev(state, questions):
    body = json.dumps({"model": "jev-latest", "state": state, "questions": questions}).encode()
    req = urllib.request.Request(
        API_URL, data=body,
        headers={"Authorization": f"Bearer {os.environ['TYPESAFE_API_KEY']}",
                 "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=25) as res:
        return json.load(res)["answers"]


def judge(puzzle, question):
    state = {
        "問題文(プレイヤーに公開済み)": puzzle["story"],
        "真相(プレイヤーには秘密)": puzzle["truth"],
        "プレイヤーの質問": question,
    }
    a = jev(state, {
        "answer": {"type": "choice", "instructions": "真相に照らして、プレイヤーの質問に出題者としてどう答えるべきか",
                   "criteria": {"yes": "真相と一致する。はい", "no": "真相と矛盾する。いいえ",
                                "irrelevant": "真相を知っていても答えが決まらない、または真相と無関係"}},
        "solved": {"type": "noul", "instructions": "プレイヤーの発言は、真相の理由の全体(なぜそうなったか)を正しく言い当てているか。部分だけ当たっている場合は否"},
        "hot": {"type": "noul", "instructions": "この質問は真相に近づく良い質問か"},
    })
    return {"label": LABELS[a["answer"]["choice"]], "confidence": a["answer"]["confidence"],
            "solved": a["solved"]["noul"], "hot": a["hot"]["noul"]}


class handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(200, [{"title": p["title"], "story": p["story"]} for p in PUZZLES])

    def do_POST(self):
        import time
        try:
            n = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(n) or b"{}")
            p = PUZZLES[int(req["puzzle"])]
            if req.get("reveal"):
                return self._send(200, {"truth": p["truth"]})
            q = str(req.get("question", "")).strip()[:300]
            if not q:
                return self._send(400, {"error": "question required"})
            t = time.time()
            out = judge(p, q)
            out["ms"] = int((time.time() - t) * 1000)
            if out["solved"] >= 0.7:
                out["truth"] = p["truth"]
            self._send(200, out)
        except Exception as e:
            self._send(500, {"error": str(e)})
