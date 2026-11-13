
const ADMIN_ID = "9076176030";

export default {
  async fetch(request, env) {

    if (request.method === "GET") {
      return new Response("TELLIBOT is running!");
    }

    if (request.method !== "POST") {
      return new Response("Not allowed", { status: 405 });
    }

    let update;

    try {
      update = await request.json();
    } catch {
      return new Response("Invalid JSON", { status: 400 });
    }

    const msg = update.message;

    if (!msg?.text) return new Response("OK");

    const chatId = msg.chat.id;
    const userId = String(msg.from.id);
    const text = msg.text.trim();

    // Send Telegram message
    async function send(message) {
      return fetch(
        `https://api.telegram.org/bot${env.BOT_TOKEN}/sendMessage`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json"
          },
          body: JSON.stringify({
            chat_id: chatId,
            text: message,
            disable_web_page_preview: true
          })
        }
      );
    }

    // Get links from KV
    async function getLinks() {
      return await env.LINKS.get("all", "json") || [];
    }

    // Save links in KV
    async function saveLinks(links) {
      await env.LINKS.put("all", JSON.stringify(links));
    }

    // User starts bot
    if (text === "/start") {

      const links = await getLinks();

      if (!links.length) {
        await send("👋 Welcome!\n\nAbhi koi link available nahi hai.");
      } else {

        for (let i = 0; i < links.length; i += 10) {

          const batch = links.slice(i, i + 10);

          let output = "👋 Welcome!\n\n";

          batch.forEach((link, j) => {
            output += `${i + j + 1}. ${link.title}\n${link.url}\n\n`;
          });

          await send(output);
        }
      }

      return new Response("OK");
    }

    // Only admin can use commands below
    if (userId !== ADMIN_ID) {
      await send("Welcome! Links ke liye /start bhejo.");
      return new Response("OK");
    }

    // Admin help
    if (text === "/help") {
      await send(
        "👑 TELLIBOT ADMIN\n\n" +
        "/addlink URL | TITLE\n" +
        "/listlinks\n" +
        "/dellink NUMBER"
      );
    }

    // Add link
    else if (text.startsWith("/addlink ")) {

      const parts = text.substring(9).split("|");

      const url = parts[0]?.trim();
      const title = parts.slice(1).join("|").trim();

      if (!/^https?:\/\/\S+$/i.test(url || "") || !title) {

        await send(
          "❌ Wrong format!\n\n" +
          "/addlink https://example.com | My Link"
        );

      } else {

        const links = await getLinks();

        links.push({ title, url });

        await saveLinks(links);

        await send("✅ Link added: " + title);
      }
    }

    // List links
    else if (text === "/listlinks") {

      const links = await getLinks();

      if (!links.length) {
        await send("No links found.");
      } else {

        const output = links.map((x, i) =>
          `${i + 1}. ${x.title}\n${x.url}`
        ).join("\n\n");

        await send(output);
      }
    }

    // Delete link
    else if (text.startsWith("/dellink")) {

      const number = Number(text.split(/\s+/)[1]);

      const links = await getLinks();

      if (
        !Number.isInteger(number) ||
        number < 1 ||
        number > links.length
      ) {

        await send("Use: /dellink 1");

      } else {

        const removed = links.splice(number - 1, 1)[0];

        await saveLinks(links);

        await send("🗑 Deleted: " + removed.title);
      }
    }

    return new Response("OK");
  }
};
